# -*- coding: utf-8 -*-
from sceptre.hooks import Hook


class ECSCluster(Hook):
    """
    Check if the specified ecs cluster exists.  If not, create it.
    """

    def __init__(self, *args, **kwargs):
        super(ECSCluster, self).__init__(*args, **kwargs)

    def run(self):
        cluster_name = self.argument
        response = self.connection_manager.call(
            service="ecs",
            command="describe_clusters",
            kwargs=dict(
                clusters=[cluster_name]
            )
        )
        if (response['clusters'] 
            and response['clusters'][0]["clusterName"] == cluster_name
        ):
            self.logger.debug("{} - Found ECS Cluster: {}".format(
                __name__, response['clusters'][0]["clusterArn"])
            )
        else:
            response = self.connection_manager.call(
                service="ecs",
                command="create_cluster",
                kwargs=dict(
                    clusterName=cluster_name
                )
            )
            self.logger.debug("{} - Created ECS Cluster {}".format(
                __name__, response["cluster"]["clusterArn"])
            )

