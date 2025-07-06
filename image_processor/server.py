from concurrent import futures
import logging
import grpc
import time

from src.generated import processing_pb2
from src.generated import processing_pb2_grpc
from src.shared.image_processing import calculate_average_intensity

class ImageProcessorServicer(processing_pb2_grpc.ImageProcessorServicer):
    """Provides methods that implement functionality of image processor server."""

    def AnalyzeImage(self, request, context):
        """Processes the image and returns the analysis."""
        try:
            result = calculate_average_intensity(request.image_data, request.allowed_formats)
            return processing_pb2.AnalysisResponse(
                average_intensity=result["average_intensity"],
                width=result["image_size"][0],
                height=result["image_size"][1],
                original_mode=result["original_mode"],
                pixel_count=result["pixel_count"],
            )
        except ValueError as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            return processing_pb2.AnalysisResponse()

def serve():
    """Starts the gRPC server."""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    processing_pb2_grpc.add_ImageProcessorServicer_to_server(ImageProcessorServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    logging.info("Image Processor gRPC server started on port 50051.")
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    serve()
