

# ----------------------- fluxity funcs
def init_script(fctx):
    fctx.set_name("Text")
    fctx.set_author("Janne Liljeblad")
 
    fctx.add_editor("Font", fctx.EDITOR_PANGO_FONT, fctx.EDITOR_PANGO_FONT_DEFAULT_VALUES)
    fctx.add_editor("Text", fctx.EDITOR_TEXT, "Text")
    
def init_render(fctx):
    # Get editor values
    font_data = fctx.get_editor_value("Font")
    text_layout = fctx.create_text_layout(font_data)
    fctx.set_data_obj("text_layout", text_layout )
        
def render_frame(frame, fctx, w, h):
    cr = fctx.get_frame_cr()

    text_layout = fctx.get_data_obj("text_layout")
    text = fctx.get_editor_value("Text")
    text_layout.draw_layout(text, cr, 100, 100)


