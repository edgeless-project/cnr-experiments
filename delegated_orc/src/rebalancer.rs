// SPDX-FileCopyrightText: © 2024 Claudio Cicconetti <c.cicconetti@iit.cnr.it>
// SPDX-License-Identifier: MIT

use edgeless_orc::proxy::Proxy;

struct NodeDesc {
    function_instances: Vec<edgeless_api::function_instance::ComponentId>,
    capabilities: edgeless_api::node_registration::NodeCapabilities,
    resource_providers: std::collections::HashSet<String>,
    fair_share: f64,
}

impl NodeDesc {
    fn credit(&self) -> i32 {
        (self.function_instances.len() as f64 - self.fair_share).round() as i32
    }
}

struct InstanceDesc {
    runtime: String,
    deployment_requirements: edgeless_orc::deployment_requirements::DeploymentRequirements,
}

pub struct Rebalancer {
    proxy: edgeless_orc::proxy_redis::ProxyRedis,
    nodes: std::collections::HashMap<edgeless_api::function_instance::NodeId, NodeDesc>,
    instances:
        std::collections::HashMap<edgeless_api::function_instance::ComponentId, InstanceDesc>,
}

impl Rebalancer {
    pub fn new(redis_url: &str) -> anyhow::Result<Self> {
        let proxy = match edgeless_orc::proxy_redis::ProxyRedis::new(redis_url, false, None) {
            Ok(proxy) => proxy,
            Err(err) => anyhow::bail!("could not connect to a Redis at {}: {}", redis_url, err),
        };
        Ok(Self {
            proxy,
            nodes: std::collections::HashMap::new(),
            instances: std::collections::HashMap::new(),
        })
    }

    pub fn rebalance(&mut self) -> (bool, usize) {
        if !self
            .proxy
            .updated(edgeless_orc::proxy::Category::NodeCapabilities)
            && !self
                .proxy
                .updated(edgeless_orc::proxy::Category::ResourceProviders)
            && !self
                .proxy
                .updated(edgeless_orc::proxy::Category::ActiveInstances)
        {
            log::info!("Nothing changed: do nothing");
            return (false, 0);
        }

        // Fetch the status of nodes.
        self.update_node_desc();

        // Assign the fair share of load to each node.
        self.assign_fair_share();

        // Try to rebalance things.
        (true, self.matching())
    }

    fn update_node_desc(&mut self) {
        // Create node descriptors, with capabilities.
        self.nodes.clear();
        for (node_id, capabilities) in self.proxy.fetch_node_capabilities() {
            self.nodes.insert(
                node_id,
                NodeDesc {
                    function_instances: vec![],
                    capabilities,
                    resource_providers: std::collections::HashSet::new(),
                    fair_share: 0.0,
                },
            );
        }

        // Add function instances.
        let mut instances = self.proxy.fetch_nodes_to_instances();
        for (node_id, instances) in &mut instances {
            let node_function_instances = &mut self
                .nodes
                .get_mut(node_id)
                .expect("cannot find node")
                .function_instances;
            for instance in instances {
                if let edgeless_orc::proxy::Instance::Function(lid) = instance {
                    node_function_instances.push(*lid);
                }
            }
        }

        // Add resource providers.
        let providers = self.proxy.fetch_resource_providers();
        for (provider_id, resource_provider) in providers {
            let node_resource_providers = &mut self
                .nodes
                .get_mut(&resource_provider.node_id)
                .expect("cannot find node")
                .resource_providers;
            node_resource_providers.insert(provider_id);
        }
    }

    fn assign_fair_share(&mut self) {
        self.instances.clear();

        let mut fair_shares = std::collections::HashMap::new();
        for node_id in self.nodes.keys() {
            fair_shares.insert(*node_id, 0.0);
        }

        let mut instances = self.proxy.fetch_function_instance_requests();
        for (lid, req) in &mut instances {
            let runtime = req.spec.function_type.clone();
            let deployment_requirements =
                edgeless_orc::deployment_requirements::DeploymentRequirements::from_annotations(
                    &req.annotations,
                );
            let mut num_feasible = 0;
            let mut feasible_nodes = vec![];
            for (node_id, node_desc) in &self.nodes {
                if edgeless_orc::orchestration_logic::OrchestrationLogic::is_node_feasible(
                    &runtime,
                    &deployment_requirements,
                    node_id,
                    &node_desc.capabilities,
                    &node_desc.resource_providers,
                ) {
                    feasible_nodes.push(*node_id);
                    num_feasible += 1;
                }
            }
            self.instances.insert(
                *lid,
                InstanceDesc {
                    runtime,
                    deployment_requirements,
                },
            );
            for feasible_node in feasible_nodes {
                *fair_shares
                    .get_mut(&feasible_node)
                    .expect("node disappeared") += 1.0 / num_feasible as f64;
            }
        }

        for (node_id, fair_share) in fair_shares {
            self.nodes
                .get_mut(&node_id)
                .expect("node disappeared")
                .fair_share = fair_share;
        }
    }

    fn matching(&mut self) -> usize {
        // Temporary credit/debit table.
        let mut credits = std::collections::HashMap::new();
        for (node_id, node_desc) in &self.nodes {
            credits.insert(node_id, node_desc.credit());
        }

        // Determine migrations to be performed.
        let mut migrations = vec![];
        for (node_id, node_desc) in &self.nodes {
            // Try to give away credit to nodes with deficit.
            for lid in &node_desc.function_instances {
                if *credits.get_mut(node_id).unwrap() <= 0 {
                    break;
                }

                let instance_desc = self
                    .instances
                    .get(lid)
                    .expect("function instance disappeared");

                // Try to assign this function instance to the first that
                // - is in deficit;
                // - can host the function.
                for (target_node_id, target_node_desc) in &self.nodes {
                    if target_node_desc.credit() < 0
                        && edgeless_orc::orchestration_logic::OrchestrationLogic::is_node_feasible(
                            &instance_desc.runtime,
                            &instance_desc.deployment_requirements,
                            target_node_id,
                            &target_node_desc.capabilities,
                            &target_node_desc.resource_providers,
                        )
                    {
                        migrations.push(edgeless_orc::deploy_intent::DeployIntent::Migrate(
                            *lid,
                            vec![*target_node_id],
                        ));
                        *credits.get_mut(node_id).unwrap() -= 1;
                        *credits.get_mut(target_node_id).unwrap() += 1;

                        break;
                    }
                }
            }
        }

        // Perform the migrations.
        let num_migrations = migrations.len();
        self.proxy.add_deploy_intents(migrations);

        num_migrations
    }
}
