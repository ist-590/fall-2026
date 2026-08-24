function Pandoc(doc)
  local result = {}
  local slides = {}
  local current_slide = {number = 1, has_note = false, note = nil}
  
  for i, block in ipairs(doc.blocks) do
    if block.t == 'Div' and block.classes[1] == 'notes' then
      current_slide.has_note = true
      current_slide.note = block.content
      
    elseif block.t == 'HorizontalRule' then
      -- Save current slide
      table.insert(slides, current_slide)
      -- Start new slide
      current_slide = {number = current_slide.number + 1, has_note = false, note = nil}
    end
  end
  
  -- Don't forget the last slide
  table.insert(slides, current_slide)
  
  -- Generate output
  for _, slide in ipairs(slides) do
    if slide.has_note and slide.note then
      -- Add slide number to first paragraph
      local first_para = true
      for _, item in ipairs(slide.note) do
        if item.t == 'Para' and first_para then
          local new_para = pandoc.Para({pandoc.Str(slide.number .. ". ")})
          for _, inline in ipairs(item.content) do
            table.insert(new_para.content, inline)
          end
          table.insert(result, new_para)
          first_para = false
        else
          table.insert(result, item)
        end
      end
    else
      -- No note for this slide
      table.insert(result, pandoc.Para{pandoc.Str(slide.number .. ". ")})
    end
    
    table.insert(result, pandoc.Para{pandoc.Str("")})
  end
  
  return pandoc.Pandoc(result, doc.meta)
end