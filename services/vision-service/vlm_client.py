from models import BBox, LocateResponse


class VLMClient:
    
    async def locate(self, image: str, action: str) -> LocateResponse:
        
        x1 = 1
        y1 = 1
        x2 = 1
        y2 = 1

        return LocateResponse(
            bbox=BBox(
                x1=x1,
                y1=y1,
                x2=x2,
                y2=y2
            )
        )
