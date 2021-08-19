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
    content = document.createElement('a')
    content.innerHTML = r.item.title
    content.href = r.item.path
    wrapper.appendChild(content)
    wrapper.className = "article"
    results.appendChild(wrapper)
  })
}

searchBar.addEventListener('keyup', callback)
