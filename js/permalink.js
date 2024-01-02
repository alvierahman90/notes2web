'use strict';

const MANUAL_REDIRECT = document.getElementById('manual_redirect');

const newLocation = data[new URLSearchParams(window.location.search).get('uuid')];

MANUAL_REDIRECT.href = newLocation;
window.location = newLocation;
