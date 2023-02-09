# Expose S3 Bucket over HTTP using AWS Lambda and the Serverless Framework

This code allows you to export an S3 bucket over HTTP endpoints.

## Usage

### Local setup

Clone code, bring in dependencies and customize configuration file.

```bash
$ git clone git@github.com:kiinoda/expose-s3-bucket.git expose-s3-bucket
$ cd expose-s3-bucket
$ cp serverless.yml.sample serverless.yml
... update ENV vars to reflect your situation
... make sure the prefix DOES NOT START with a /
... make sure the prefix ENDS with /
$ npm install
```

### Deployment

```bash
$ npx sls deploy
...
```

After deploying, you should see output similar to:

```bash

Deploying expose-s3-bucket to stage dev (eu-west-1)

✔ Service deployed to stack expose-s3-bucket-dev (50s)

api keys:
  bk_key: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
endpoints:
  GET - https://XXXXXXXXXX.execute-api.eu-west-1.amazonaws.com/dev/list
  GET - https://XXXXXXXXXX.execute-api.eu-west-1.amazonaws.com/dev/get
functions:
  list: expose-s3-bucket-dev-list (541 kB)
  get: expose-s3-bucket-dev-get (541 kB)
```

### Invocation

After successful deployment, you can list the files in the bucket via HTTP:

```bash
curl -sH 'x-api-key: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX' https://XXXXXXXXXX.execute-api.eu-west-1.amazonaws.com/dev/list?date=2023
```

Which should result in response similar to the following:

```json
{
  "files": [
    {
      "file": "2023/01/31/test.json",
      "size": 10
    },
    {
      "file": "2023/01/31/test1.json",
      "size": 10
    }
  ]
}
```

You should then be able to retrieve one of the files you're interested by issuing a get like this:

```bash
curl -sH 'x-api-key: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX' https://XXXXXXXXXX.execute-api.eu-west-1.amazonaws.com/dev/get?file=2023/01/31/test.json
```

That's about it. Enjoy!
