-- tocEpub.lua -- a Pandoc filter used by buildBooks for every MyBooks EPUB.
-- 1. Replaces a paragraph that reads [TOC] with a linked list of the book's chapter headings, so the contents page works in any reader.
-- 2. Drops a horizontal rule that only separates one section from the next heading or ends the book, since each chapter starts a new page anyway.
-- The heading level listed is the highest one the book uses for its sections, which is the level each EPUB page starts with.

local c_sTocMarker = "[TOC]"

function isSkipped(sText)
  local sLower = string.lower(sText)
  return sLower == "table of contents" or sLower == "contents" or sLower == "copyright"
end

function Pandoc(doc)
  local iLevel = 6
  for _, oBlock in ipairs(doc.blocks) do
    if oBlock.t == "Header" and oBlock.level < iLevel then iLevel = oBlock.level end
  end
  local lItems = {}
  for _, oBlock in ipairs(doc.blocks) do
    if oBlock.t == "Header" and oBlock.level == iLevel and oBlock.identifier ~= "" and not isSkipped(pandoc.utils.stringify(oBlock.content)) then
      table.insert(lItems, {pandoc.Plain({pandoc.Link(oBlock.content, "#" .. oBlock.identifier)})})
    end
  end
  local lBlocks = {}
  for i, oBlock in ipairs(doc.blocks) do
    local oNext = doc.blocks[i + 1]
    if oBlock.t == "Para" and pandoc.utils.stringify(oBlock) == c_sTocMarker then
      if #lItems > 0 then table.insert(lBlocks, pandoc.BulletList(lItems)) end
    elseif oBlock.t == "HorizontalRule" and (oNext == nil or oNext.t == "Header") then
      -- a separator before a new section adds nothing in an EPUB
    else
      table.insert(lBlocks, oBlock)
    end
  end
  doc.blocks = lBlocks
  return doc
end
