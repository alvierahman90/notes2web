const HEADERS = "headers"
const PATH = "path"
const TAGS = "tags"
const TITLE = "title"

const SEARCH_TIMEOUT_MS = 100
var SEARCH_TIMEOUT_ID = -1

const fuse = new Fuse(data, {
  keys: [ 'title' ],
  ignoreLocation: true,
  threshhold: 0.4,
  minMatchCharLength: 0,
})

const RESULTS_MAX = 15

const searchBar = document.getElementById('search')
const resultsDiv = document.getElementById('searchResults')

var results = []

function updateResultsWithTimeout() {
  console.log("clearing timeout")
  if (SEARCH_TIMEOUT_ID) SEARCH_TIMEOUT_ID = clearTimeout(SEARCH_TIMEOUT_ID)
  SEARCH_TIMEOUT_ID = setTimeout(updateResults, SEARCH_TIMEOUT_MS)
}

function updateResults() {
  console.log("updating results")
  resultsDiv.innerHTML = ''
  if (searchBar.value) results = fuse.search(searchBar.value, { limit: RESULTS_MAX }).map(r => r.item)
  else results = data

  results.forEach(r => {
    wrapper = document.createElement('li')
    wrapper.className = "article"

    atag = document.createElement('a')
    atag.href = r.path

    ptag = document.createElement('p')
    ptag.innerHTML = r.title + (r.isdirectory ? '/' : '')

    atag.appendChild(ptag)
    wrapper.appendChild(atag)
    resultsDiv.appendChild(wrapper)
  })
}

searchBar.addEventListener('keyup', e => {
  console.log(e)
  // if user pressed enter
  if (e.keyCode === 13) {
    if (e.shiftKey) {
      window.open(results[0].path, '_blank')
    } else {
    window.location.href = results[0].path
    }
    return
  }
  updateResultsWithTimeout()
})

searchBar.addEventListener('change', updateResultsWithTimeout)

const searchParams = new URL(window.location.href).searchParams;
searchBar.value = searchParams.get('q');
updateResults();

console.log(results)

if (searchParams.has('lucky')) {
  window.location.href = results[0].path;
}
