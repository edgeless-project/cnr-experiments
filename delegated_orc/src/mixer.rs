// SPDX-FileCopyrightText: © 2024 Claudio Cicconetti <c.cicconetti@iit.cnr.it>
// SPDX-License-Identifier: MIT

use edgeless_api::outer::controller::ControllerAPI;
use edgeless_api::workflow_instance::WorkflowInstanceAPI;
use edgeless_orc::proxy::Proxy;
use rand::Rng;

pub struct Mixer {
    /// The client interface.
    client: Box<dyn WorkflowInstanceAPI>,
    /// The orchestrator proxy.
    proxy: edgeless_orc::proxy_redis::ProxyRedis,
    /// The name of the function to be migrated.
    function: String,
    /// The label to be matched, if non-empty.
    label: String,

    rng: rand::rngs::ThreadRng,
}

impl Mixer {
    pub async fn new(
        controller_url: &str,
        redis_url: &str,
        function: &str,
        label: &str,
    ) -> anyhow::Result<Self> {
        let proxy = match edgeless_orc::proxy_redis::ProxyRedis::new(redis_url, false, None) {
            Ok(proxy) => proxy,
            Err(err) => anyhow::bail!("could not connect to a Redis at {}: {}", redis_url, err),
        };
        Ok(Self {
            client: edgeless_api::grpc_impl::outer::controller::ControllerAPIClient::new(
                controller_url,
            )
            .await
            .workflow_instance_api(),
            proxy,
            function: function.to_string(),
            label: label.to_string(),
            rng: rand::thread_rng(),
        })
    }

    /// Randomly assign functions to nodes.
    ///
    /// Return the number of functions migrated.
    pub async fn mix(&mut self) -> usize {
        // Find all the function instances with matching name.
        let mut lids = vec![];
        let workflow_ids = self.client.list().await.expect("could not list workflows");
        for workflow_id in workflow_ids {
            let workflow_info = self
                .client
                .inspect(workflow_id)
                .await
                .expect("could not inspect workflow");

            for mapping in workflow_info.status.domain_mapping {
                if mapping.name == self.function {
                    lids.push(mapping.function_id);
                }
            }
        }

        // Find all the nodes.
        let mut node_ids = vec![];
        for (node_id, capabilities) in self.proxy.fetch_node_capabilities() {
            // Skip node if it does not match the given label.
            if !self.label.is_empty() {
                if !capabilities.labels.contains(&self.label) {
                    continue;
                }
            }

            node_ids.push(node_id);
        }

        if lids.is_empty() || node_ids.len() <= 1 {
            return 0;
        }

        // Migrate all function instances.
        let mut num_migrations = 0;
        for lid in lids {
            let target_node_ndx = self.rng.gen_range(0..node_ids.len());
            let target_node_id = node_ids[target_node_ndx];
            self.proxy.add_deploy_intents(vec![
                edgeless_orc::deploy_intent::DeployIntent::Migrate(lid, vec![target_node_id]),
            ]);
            num_migrations += 1;
        }

        num_migrations
    }
}
