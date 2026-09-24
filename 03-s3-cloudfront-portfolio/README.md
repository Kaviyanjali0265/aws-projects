# Project 3 - Static Portfolio with S3 + CloudFront

## What This Project Does

Hosts a static portfolio website on Amazon S3 and serves it globally through CloudFront. S3 is kept fully private - only CloudFront can read from it using OAC (Origin Access Control). Users always get HTTPS even though S3 only stores plain files.

---

## Architecture

```
Internet
    |
    | HTTPS (port 443)
    v
CloudFront Distribution
    |   215+ edge locations worldwide
    |   Price Class 100 (North America + Europe - cheapest)
    |   Default root object: index.html
    |   Viewer protocol: HTTP redirected to HTTPS
    |   Free HTTPS on *.cloudfront.net (no custom domain needed)
    |
    |-- Cache HIT  → returns cached index.html from edge immediately
    |-- Cache MISS → fetches from S3, caches at edge, returns to user
    |
    | OAC signs every request with SigV4
    | (only CloudFront can produce this signature)
    v
S3 Bucket: kaviyanjali-portfolio
    |   Region: ap-south-1
    |   Block Public Access: ON
    |   Direct S3 URL → 403 Access Denied
    |   Bucket policy: allows s3:GetObject only from this CloudFront distribution
    |
    |   index.html  ← portfolio page
    v
OAC (Origin Access Control)
    Type: S3
    Signing: SigV4, always
    Purpose: CloudFront signs S3 requests → S3 verifies → allows access
```

---

## Key AWS Services Used

| Service | Purpose |
|---------|---------|
| S3 | Stores static files (HTML, CSS, JS) - kept private |
| CloudFront | CDN - serves content from edge locations globally, handles HTTPS |
| OAC | Lets CloudFront authenticate to S3 without making S3 public |
| ACM | Free SSL certificate (must be in us-east-1 for CloudFront) - optional for custom domain |

---


## How It Was Built

### Step 1 - S3 Bucket

- Created bucket `kaviyanjali-portfolio` in ap-south-1
- Block Public Access: ON (bucket stays private)
- Uploaded `app/index.html`

### Step 2 - CloudFront Distribution

- Origin: `kaviyanjali-portfolio` S3 bucket
- Origin access: OAC (auto-created by console)
- Default root object: `index.html`
- Viewer protocol policy: Redirect HTTP to HTTPS
- Price class: 100 (cheapest - North America + Europe edge locations)
- CloudFront auto-generates the bucket policy → paste into S3

### Step 3 - S3 Bucket Policy

Applied the policy CloudFront generated:

```json
{
  "Effect": "Allow",
  "Principal": { "Service": "cloudfront.amazonaws.com" },
  "Action": "s3:GetObject",
  "Resource": "arn:aws:s3:::kaviyanjali-portfolio/*",
  "Condition": {
    "StringEquals": {
      "AWS:SourceArn": "arn:aws:cloudfront::<account-id>:distribution/<distribution-id>"
    }
  }
}
```

Only this specific CloudFront distribution can read from S3. All other requests return 403.

### Step 4 - Wait for Deployment

CloudFront takes 5–10 minutes to deploy to all edge locations. Status changes from "Deploying" to "Enabled".

---

## Traffic Flow

```
User opens https://d1234abc.cloudfront.net
    → DNS resolves to nearest CloudFront edge location
    → Edge checks cache for index.html
    │
    ├── Cache HIT (TTL not expired)
    │       → Returns cached file immediately
    │       → S3 never contacted
    │
    └── Cache MISS (first request or TTL expired)
            → CloudFront fetches from S3
            → Signs request with OAC (SigV4 signature)
            → S3 verifies signature → allows access
            → CloudFront caches file at edge
            → Returns to user
```

## Why Direct S3 URL is Blocked

```
User tries: https://kaviyanjali-portfolio.s3.ap-south-1.amazonaws.com/index.html
    → S3 checks bucket policy
    → Request has no OAC signature
    → No condition match
    → Returns 403 Access Denied

Only CloudFront signs requests with OAC → only CloudFront gets through
```

---

## Files

```
03-s3-cloudfront-portfolio/
├── app/
│   └── index.html              # Portfolio page - dark theme, project cards, skills grid
├── cloudformation/
│   └── template.yaml           # S3 bucket, OAC, CloudFront distribution as code
└── screenshots/
    └── (added after CloudFront verification)
```

---

## Key Concepts Demonstrated

**OAC vs making S3 public** - S3 stays fully private. OAC gives CloudFront a signed identity so S3 can verify "this request came from my CloudFront distribution". No public bucket needed.

**CloudFront caching** - Static files are cached at edge locations. Users in any region get fast response without every request hitting S3 in Mumbai.

**HTTPS for free** - CloudFront gives HTTPS on `*.cloudfront.net` automatically. No ACM certificate needed unless you use a custom domain.

**ACM must be us-east-1** - CloudFront is a global service that reads certificates only from us-east-1, even if your S3 bucket is in another region.

**Price Class 100** - Limits edge locations to North America + Europe (cheapest). Price Class 200 adds more regions, All adds every location.

---

## Deploy with CloudFormation

```bash
aws cloudformation create-stack \
  --stack-name project3-cloudfront \
  --template-body file://cloudformation/template.yaml \
  --profile personal
```

Then upload the portfolio page:

```bash
aws s3 cp app/index.html s3://kaviyanjali-portfolio/ --profile personal
```

---

## Alternative with Route 53 (not used - costs money)

```
Custom domain: kaviya.com
    → Route 53 hosted zone ($0.50/month)
    → Alias record pointing to CloudFront distribution
    → ACM certificate in us-east-1 (free)
    → Same CloudFront + S3 flow as above
```
