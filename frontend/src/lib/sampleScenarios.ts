// Preset demo scenarios for the public self-serve audit page.
// Policy stays constant across scenarios; only the config varies so
// visitors can compare outcomes against the same 4 rules.

const POLICY = `Company Security Policy:
1. All S3 buckets must have 'encryption' set to 'AES256'.
2. All S3 buckets must have 'public_access' set to 'false'.
3. All EC2 instances must have 'subnet_type' set to 'private'.
4. All IAM users must have 'mfa_enabled' set to 'true'.`;

export interface SampleScenario {
  id: string;
  label: string;
  description: string;
  policy: string;
  config: string;
}

export const SAMPLE_SCENARIOS: SampleScenario[] = [
  {
    id: "mixed",
    label: "Mixed Results",
    description: "3 passes, 4 violations across S3, EC2 and IAM",
    policy: POLICY,
    config: JSON.stringify(
      {
        aws_configuration: {
          s3_buckets: [
            { name: "s3-bucket-logs", encryption: null, public_access: false },
            { name: "s3-bucket-public", encryption: "AES256", public_access: true },
          ],
          ec2_instances: [{ instance_id: "i-12345", subnet_type: "public" }],
          iam_users: [
            { username: "bob", mfa_enabled: true },
            { username: "alice", mfa_enabled: false },
          ],
        },
      },
      null,
      2
    ),
  },
  {
    id: "clean",
    label: "Fully Compliant",
    description: "Every resource passes all 4 rules",
    policy: POLICY,
    config: JSON.stringify(
      {
        aws_configuration: {
          s3_buckets: [{ name: "s3-bucket-clean", encryption: "AES256", public_access: false }],
          ec2_instances: [{ instance_id: "i-99999", subnet_type: "private" }],
          iam_users: [{ username: "carol", mfa_enabled: true }],
        },
      },
      null,
      2
    ),
  },
  {
    id: "single-violation",
    label: "Single Critical Violation",
    description: "One public S3 bucket, everything else compliant",
    policy: POLICY,
    config: JSON.stringify(
      {
        aws_configuration: {
          s3_buckets: [{ name: "prod-data-bucket", encryption: "AES256", public_access: true }],
          ec2_instances: [{ instance_id: "i-55555", subnet_type: "private" }],
          iam_users: [{ username: "dave", mfa_enabled: true }],
        },
      },
      null,
      2
    ),
  },
];
