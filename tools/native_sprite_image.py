"""Decode immutable GX conventional-memory AND/OR images, not screenshots."""
from PIL import Image

EGA = [(0,0,0),(0,0,170),(0,170,0),(0,170,170),(170,0,0),(170,0,170),(170,85,0),(170,170,170),
       (85,85,85),(85,85,255),(85,255,85),(85,255,255),(255,85,85),(255,85,255),(255,255,85),(255,255,255)]


def decode(body, mask):
    assert (body['width'],body['height'],body['planes']) == (mask['width'],mask['height'],4)
    def pixel(source,x,y):
        return sum(((source['data'][(y*source['planes']+p)*source['storage_stride']+x//8] >> (7-x%8)) & 1) << p
                   for p in range(source['planes']))
    image = Image.new('RGBA',(body['width'],body['height']))
    for y in range(image.height):
        for x in range(image.width):
            b,m = pixel(body,x,y),pixel(mask,x,y)
            if m == 15 and b == 0:
                value = (0,0,0,0)
            elif m == 0:
                value = EGA[b]+(255,)
            else:
                raise ValueError('This AND/OR pixel needs destination-dependent compositing')
            image.putpixel((x,y),value)
    return image
