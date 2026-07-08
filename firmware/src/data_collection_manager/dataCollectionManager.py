import rclpy
from rclpy.node import Node

from std_srvs.srv import SetBool
from std_msgs.msg import Bool


class DataCollectionManager(Node):
    def __init__(self):
        super().__init__("data_collection_manager")
        
        self.collection_enabled = False

        self.publisher = self.create_publisher(Bool, "/data_collection_enabled", 10)
        
        self.srv = self.create_service(
            SetBool, "/set_data_collection_enaled", self.set_collection_enabled
        )

    def set_collection_enabled(self, request, response):
        self.collection_enabled = request.data
        
        msg = Bool()
        msg.data = self.collection_enabled
        self.publisher.publish(msg)
        
        response.success = True
        response.message = "Data collection started" if self.collection_enabled else "Data collection stopped"
        
        return response
    
def main():
    rclpy.init()
    node = DataCollectionManager()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
    
if __name__ == "__maain__":
    main()
