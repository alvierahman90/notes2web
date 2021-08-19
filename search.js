const fuse = new Fuse(data, {
  keys: ['path', 'title', 'tags']
})

const searchBar = document.getElementById('search')
const results = document.getElementById('results')

function callback() {
  console.log("called")
  console.log(searchBar.value)
  results.innerHTML = ''
  fuse.search(searchBar.value).forEach(r => {
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

    content = document.createElement('a')
    content.innerHTML = r.item.title
    content.href = r.item.path

    wrapper.appendChild(content)
    wrapper.appendChild(extra_info)

    results.appendChild(wrapper)
  })
}

searchBar.addEventListener('keyup', callback)
callback()
