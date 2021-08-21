const HEADERS = "headers"
const PATH = "path"
const TAGS = "tags"
const TITLE = "title"

const fuse = new Fuse(data, {
  keys: [ HEADERS, PATH, TAGS, TITLE ],
  includeMatches: true
})

const searchBar = document.getElementById('search')
const results = document.getElementById('results')

function callback() {
  results.innerHTML = ''
  fuse.search(searchBar.value).slice(0,15).forEach(r => {
    wrapper = document.createElement('div')
    wrapper.className = "article"

    display_matches = {}
    display_matches[HEADERS] = []
    display_matches[PATH] = []
    display_matches[TAGS] = []
    display_matches[TITLE] = []

    r.matches.every(match => {
      if (display_matches[match.key].length > 3) {
        display_matches[match.key].push('...')
        return false
      }

      display_match = match.value
      if (match.indices.length >= 1) {
        match.indices.sort((a, b) => (b[1]-b[0])-(a[1]-a[0]))
        indexPair = match.indices[0]
        matching_slice = match.value.slice(indexPair[0], indexPair[1]+1)
        display_match = match.value.replace(
          matching_slice,
          '<span class="matchHighlight">' + matching_slice + '</span>'
        )
      }
      display_matches[match.key].push(display_match)

      return true
    })

    content = document.createElement('a')
    content.innerHTML = r.item.title
    content.href = r.item.path

    wrapper.appendChild(content)

    Object.keys(display_matches).forEach(key => {
      if (display_matches[key].length < 1) return

      p = document.createElement('p')
      p.className = "smallText"
      p.innerHTML += key + ": [" + display_matches[key].join(', ') + ']'
      wrapper.appendChild(p)
    })

    results.appendChild(wrapper)
  })
}

searchBar.addEventListener('keyup', callback)
callback()
