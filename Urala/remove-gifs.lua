function Image (elem)
  if FORMAT == "pdf" or FORMAT == "latex" then
    if elem.src:match("%.gif$") then
      return {} -- Remove the image
    end
  end
end