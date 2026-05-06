"""
Script to submit the Critic training job to Vertex AI.
"""

import argparse
from google.cloud import aiplatform


def submit_training_job(
    project_id: str,
    location: str,
    staging_bucket: str,
    data_bucket: str,
    image_uri: str,
    epochs: int = 50,
    batch_size: int = 64,
):
    """
    Submits a Custom Job to Vertex AI.
    """
    aiplatform.init(
        project=project_id, location=location, staging_bucket=staging_bucket
    )

    job = aiplatform.CustomContainerTrainingJob(
        display_name="maaps-critic-training",
        container_uri=image_uri,
        # The entrypoint in the Dockerfile will be executed
        command=["python", "src/agents/train_critic_remote.py"],
    )

    model = job.run(
        args=[
            f"--data-dir={data_bucket}",
            f"--epochs={epochs}",
            f"--batch-size={batch_size}",
            f"--model-dir={staging_bucket}/models",
        ],
        replica_count=1,
        machine_type="n1-standard-8",
        accelerator_type="NVIDIA_TESLA_T4",
        accelerator_count=1,
        sync=True,
    )

    print(f"Job completed. Model saved to {staging_bucket}/models")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--location", default="us-central1")
    parser.add_argument("--bucket", required=True, help="Bucket for staging and data")
    parser.add_argument("--image", required=True, help="Docker image URI")
    parser.add_argument("--epochs", type=int, default=50)

    args = parser.parse_args()

    submit_training_job(
        project_id=args.project_id,
        location=args.location,
        staging_bucket=args.bucket,
        data_bucket=args.bucket,
        image_uri=args.image,
        epochs=args.epochs,
    )
