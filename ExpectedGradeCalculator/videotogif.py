from moviepy.editor import *

clip = (VideoFileClip("Grey_Plexus_Networking.mp4").subclip(0,10))
clip.write_gif("output.gif",fps=29,program='ffmpeg')