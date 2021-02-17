# Deploying Functions

The project comes with a `serverless framework` project to deploy the functions.

Deploying the functions will require `npm` and `python/pip` to be installed.

First install `serverless framework` globally:
```sh
npm install -g serverless
```
(Global installation might require sudo)

Then clone this repository, then use `npm` to install `serverless` and it's dependencies:
```sh
npm install
```

Then use the `serverless` cli tool to deploy the stack:
```sh
serverless deploy
```

For convenience serverless provides the alias `sls` for the `serverless` command.

You can use the `info` command to get an overview of existing resources:
```sh
sls info
```