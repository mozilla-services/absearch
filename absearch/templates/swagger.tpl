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
    /:
      get:
        operationId: getRoot
        description: returns a description of the service
        produces:
        - application/json
        responses:
          '200':
            description: Description returned
    /__info__:
      get:
        operationId: getInfo
        description: returns the version info
        produces:
        - application/json
        responses:
          '200':
            description: Info returned
    /__heartbeat__:
      get:
        operationId: getHeartbeat
        description: Performs an heartbeat on the app
        produces:
        - application/json
        responses:
          '200':
            description: The hearbeat was successfull
    /1/{prod}/{ver}/{channel}/{locale}/{territory}/{dist}/{distver}:
      get:
        operationId: addUserToCohort
        description: Assign the user to a cohort and returns its settings
        produces:
        - application/json
        responses:
          '200':
            description: The cohort settings are returns
          '404':
            description: The provided path was not found
        parameters:
        - name: prod
          in: path
          description: product name
          required: true
          type: string
        - name: ver
          in: path
          description: product version
          required: true
          type: string
        - name: channel
          in: path
          description: product release channel
          required: true
          type: string
        - name: locale
          in: path
          description: client locale
          required: true
          type: string
        - name: territory
          in: path
          description: client territory
          required: true
          type: string
        - name: dist
          in: path
          description: product distribution
          required: true
          type: string
        - name: distver
          in: path
          description: product distribution version
          required: true
          type: string
    /1/{prod}/{ver}/{channel}/{locale}/{territory}/{dist}/{distver}/{cohort}:
      get:
        operationId: returnCohortSettings
        description: Returns the cohort settings
        produces:
        - application/json
        responses:
          '200':
            description: The hearbeat was successfull
          '404':
            description: The cohort was not found
        parameters:
        - name: prod
          in: path
          description: product name
          required: true
          type: string
        - name: ver
          in: path
          description: product version
          required: true
          type: string
        - name: channel
          in: path
          description: product release channel
          required: true
          type: string
        - name: locale
          in: path
          description: client locale
          required: true
          type: string
        - name: territory
          in: path
          description: client territory
          required: true
          type: string
        - name: dist
          in: path
          description: product distribution
          required: true
          type: string
        - name: distver
          in: path
          description: product distribution version
          required: true
          type: string
        - name: cohort
          in: path
          description: cohort name
          required: true
          type: string
