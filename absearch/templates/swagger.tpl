swagger: "2.0"
host: {{HOST}}
info:
  title: ABSearch Server
  description: lightweight a/b testing tool for search options
  contact:
    name: Mike Connor
    email: mconnor@mozilla.com
  license:
    name: APLv2
    url: https://www.apache.org/licenses/LICENSE-2.0.html
  version: {{VERSION}}
  x-mozilla-services:
    homepage: https://github.com/mozilla-services/absearch
schemes:
    - {{SCHEME}}
paths:
    /__heartbeat__:
      get:
        operationId: getHeartbeat
        description: Performs an heartbeat on the app
        produces:
        - application/json
        responses:
          '200':
            description: The hearbeat was successfull
