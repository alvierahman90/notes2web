const fuse = new Fuse(data, {
  keys: ['path', 'title', 'tags', 'headers'],
  includeMatches: true
})

const searchBar = document.getElementById('search')
const results = document.getElementById('results')

function callback() {
  console.log("called")
  console.log(searchBar.value)
  results.innerHTML = ''
  fuse.search(searchBar.value).forEach(r => {
    console.log(r)
    wrapper = document.createElement('div')
    wrapper.className = "article"

    extra_info = document.createElement('p')
    extra_info.className = "smallText"
    extra_info.innerHTML = "tags: "
    if (r.item.tags == null) {
      extra_info.innerHTML += "none"
    } else {
      extra_info.innerHTML += "[" + r.item.tags.join(', ') + ']'
    }
    extra_info.innerHTML += ' path: ' + r.item.path

    header_matches_p = document.createElement('p')
    header_matches_p.className = "smallText"
    header_matches = []

    r.matches.every(match => {
      if (header_matches.length > 3) {
        header_matches.push('...')
        return false
      }

      if (match.key === "headers") {
        display_match = match.value
        if (match.indices.length >= 1) {
          match.indices.sort((a, b) => (b[1]-b[0])-(a[1]-a[0]))
          indexPair = match.indices[0]
          matching_slice = match.value.slice(indexPair[0], indexPair[1]+1)
          console.log(matching_slice)
          console.log(display_match)
          display_match = display_match.replace(
            matching_slice,
            '<span class="matchHighlight">' + matching_slice + '</span>'
          )
        }
        header_matches.push(display_match)
      }
      return true
    })

    header_matches_p.innerHTML += "header_matches: [" + header_matches.join(', ') + ']'

    content = document.createElement('a')
    content.innerHTML = r.item.title
    content.href = r.item.path

    wrapper.appendChild(content)
    wrapper.appendChild(extra_info)
    if (header_matches.length > 0) {
      wrapper.appendChild(header_matches_p)
    }

    results.appendChild(wrapper)
  })
}

searchBar.addEventListener('keyup', callback)
callback()
