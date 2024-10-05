import pygame
from core_ext.texture import Texture

class TextTexture(Texture):
    """
    Define a text texture by using pygame
    """
    def __init__(self, text="Python graphics",
                 system_font_name="Arial",
                 font_file_name=None,
                 font_size=24,
                 font_color=(0, 0, 0),
                 background_color=(255, 255, 255),
                 transparent=False,
                 image_width=None,
                 image_height=None,
                 align_horizontal=0.0,
                 align_vertical=0.0,
                 image_border_width=0,
                 image_border_color=(0, 0, 0)):
        super().__init__()
        # Store parameters as instance variables
        self.text = text
        self.system_font_name = system_font_name
        self.font_file_name = font_file_name
        self.font_size = font_size
        self.font_color = font_color
        self.background_color = background_color
        self.transparent = transparent
        self.image_width = image_width
        self.image_height = image_height
        self.align_horizontal = align_horizontal
        self.align_vertical = align_vertical
        self.image_border_width = image_border_width
        self.image_border_color = image_border_color

        # Set a default font
        font = pygame.font.SysFont(system_font_name, font_size)
        # The font can be overridden by loading font file
        if font_file_name is not None:
            font = pygame.font.Font(font_file_name, font_size)
        # Render text to (antialiased) surface
        font_surface = font.render(text, True, font_color)
        # Determine size of rendered text for alignment purposes
        (text_width, text_height) = font.size(text)
        # If image dimensions are not specified,
        # use the font surface size as default
        if image_width is None:
            image_width = text_width
        if image_height is None:
            image_height = text_height
        # Create a surface to store the image of text
        # (with the transparency channel by default)
        self._surface = pygame.Surface((image_width, image_height),
                                       pygame.SRCALPHA)
        # Set a background color used when not transparent
        if not transparent:
            self._surface.fill(background_color)
        # Attributes align_horizontal, align_vertical define percentages,
        # measured from top-left corner
        corner_point = (align_horizontal * (image_width - text_width),
                        align_vertical * (image_height - text_height))
        destination_rectangle = font_surface.get_rect(topleft=corner_point)
        # Add border (optionally)
        if image_border_width > 0:
            pygame.draw.rect(self._surface, image_border_color,
                             [0, 0, image_width, image_height], image_border_width)
        # Apply font_surface to a correct position on the final surface
        self._surface.blit(font_surface, destination_rectangle)
        self.upload_data()

    def update_text(self, new_text):
        self.text = new_text
        font = pygame.font.SysFont(self.system_font_name, self.font_size)
        if self.font_file_name is not None:
            font = pygame.font.Font(self.font_file_name, self.font_size)
        font_surface = font.render(self.text, True, self.font_color)
        (text_width, text_height) = font.size(self.text)
        image_width = self.image_width if self.image_width else text_width
        image_height = self.image_height if self.image_height else text_height
        self._surface = pygame.Surface((image_width, image_height), pygame.SRCALPHA)
        if not self.transparent:
            self._surface.fill(self.background_color)
        corner_point = (self.align_horizontal * (image_width - text_width),
                        self.align_vertical * (image_height - text_height))
        destination_rectangle = font_surface.get_rect(topleft=corner_point)
        if self.image_border_width > 0:
            pygame.draw.rect(self._surface, self.image_border_color,
                             [0, 0, image_width, image_height], self.image_border_width)
        self._surface.blit(font_surface, destination_rectangle)
        self.upload_data()
