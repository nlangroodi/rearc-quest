provider "aws" {
  region = var.aws_region
}

resource "aws_s3_bucket" "data_pipeline_bucket" {
  bucket = "data-pipeline-bucket-rearc-quest-nml"
}

resource "aws_s3_bucket_lifecycle_configuration" "data_pipeline_bucket_lifecycle" {
  bucket = aws_s3_bucket.data_pipeline_bucket.id

  rule {
    id     = "expire-old-files"
    status = "Enabled"

    expiration {
      days = 30
    }
  }
}

resource "aws_sqs_queue" "data_pipeline_queue" {
  name = "data-pipeline-queue"
}

resource "aws_sqs_queue_policy" "data_pipeline_queue_policy" {
  queue_url = aws_sqs_queue.data_pipeline_queue.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = "*",
        Action = "sqs:SendMessage",
        Resource = aws_sqs_queue.data_pipeline_queue.arn,
        Condition = {
          ArnEquals = {
            "aws:SourceArn" = aws_s3_bucket.data_pipeline_bucket.arn
          }
        }
      }
    ]
  })
}

resource "aws_s3_bucket_notification" "s3_notification" {
  bucket = aws_s3_bucket.data_pipeline_bucket.id

  queue {
    queue_arn = aws_sqs_queue.data_pipeline_queue.arn
    events    = ["s3:ObjectCreated:*"]
  }
}

resource "aws_iam_role" "lambda_execution_role" {
  name = "lambda-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_policy" {
  name   = "lambda-policy"
  role   = aws_iam_role.lambda_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:*",
          "sqs:*",
          "logs:*"
        ]
        Effect   = "Allow"
        Resource = "*"
      }
    ]
  })
}

resource "aws_lambda_function" "data_pipeline_lambda" {
  function_name = "data-pipeline-lambda"
  runtime       = "python3.9"
  handler       = "scripts.aws_sync_datausa.lambda_handler"
  role          = aws_iam_role.lambda_execution_role.arn

  filename         = "${path.module}/aws_sync_datausa.zip"
  source_code_hash = filebase64sha256("${path.module}/aws_sync_datausa.zip")

  environment {
    variables = {
      BUCKET_NAME = aws_s3_bucket.data_pipeline_bucket.id
    }
  }
}

resource "aws_lambda_function" "sqs_processor_lambda" {
  function_name = "sqs-processor-lambda"
  runtime       = "python3.9"
  handler       = "scripts.sqs_processor.lambda_handler"
  role          = aws_iam_role.lambda_execution_role.arn

  filename         = "${path.module}/sqs_processor.zip"
  source_code_hash = filebase64sha256("${path.module}/sqs_processor.zip")
}

resource "aws_lambda_event_source_mapping" "sqs_to_lambda" {
  event_source_arn = aws_sqs_queue.data_pipeline_queue.arn
  function_name    = aws_lambda_function.sqs_processor_lambda.arn
}

resource "aws_cloudwatch_event_rule" "daily_schedule" {
  name        = "daily-schedule"
  description = "Triggers Lambda daily"
  schedule_expression = "rate(1 day)"
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.daily_schedule.name
  target_id = "data-pipeline-lambda"
  arn       = aws_lambda_function.data_pipeline_lambda.arn
}

resource "aws_lambda_permission" "allow_cloudwatch_to_invoke" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.data_pipeline_lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_schedule.arn
}