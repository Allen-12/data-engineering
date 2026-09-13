# AWS setup

The pipeline reads a public dataset anonymously — no AWS account needed for
that part. Writing the output requires your own AWS account, since it's
writing into your own bucket. This is a one-time setup.

## 1. Install the AWS CLI

```bash
brew install awscli
aws --version
```

## 2. Create an IAM group scoped to just this project, and a user in it

Don't reuse root/admin credentials for a portfolio project, and don't
attach policies directly to a user — policies belong on a group, so
permissions stay easy to audit and change later. This project gets its
own group so its access stays isolated from any other project's bucket.

1. In the [IAM console](https://console.aws.amazon.com/iam/groups), create
   a group named e.g. `s3-data-pipeline-dev`.
2. Attach a customer-managed policy to the **group** (replace
   `YOUR_BUCKET_NAME` with the bucket you'll create in step 3):

   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": ["s3:ListBucket"],
         "Resource": "arn:aws:s3:::YOUR_BUCKET_NAME"
       },
       {
         "Effect": "Allow",
         "Action": ["s3:GetObject", "s3:PutObject"],
         "Resource": "arn:aws:s3:::YOUR_BUCKET_NAME/*"
       }
     ]
   }
   ```

3. Create a user (e.g. `s3-data-pipeline-dev`) with **programmatic access**
   (access key, no console password needed), and add it to the
   `s3-data-pipeline-dev` group instead of attaching any policy to the
   user directly.
4. Save the generated **access key ID** and **secret access key** — you
   won't be able to see the secret again after this step.

A group per project keeps access isolated and works well for a handful of
projects. If this grows to many small projects, a single shared group with
a policy scoped per-user (e.g. via `${aws:username}` or resource tags)
scales better than creating a new group for every one.

## 3. Create the destination bucket

Bucket names are globally unique across all of AWS, so pick something
specific to you, e.g. `s3-data-pipeline-<yourname>-dev`.

```bash
aws s3 mb s3://YOUR_BUCKET_NAME --region us-east-1
```

## 4. Configure your local credentials

```bash
aws configure
```

Enter the access key ID/secret from step 2, and `us-east-1` as the default
region (or wherever you created the bucket).

Verify it worked:

```bash
aws sts get-caller-identity
aws s3 ls s3://YOUR_BUCKET_NAME
```

## 5. Point the pipeline at your bucket

```bash
cp .env.example .env
# then edit .env and set DEST_BUCKET=YOUR_BUCKET_NAME
```

You're ready to run the pipeline — see the README for how.
