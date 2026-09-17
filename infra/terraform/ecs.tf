resource "aws_ecs_cluster" "acmecorp" {
  name = "acmecorp-dev"

  tags = {
    Project     = "acmecorp-platform"
    Environment = "dev"
  }
}

resource "aws_iam_role" "ecs_task_execution" {
  name = "acmecorp-ecs-task-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"

    Statement = [{
      Effect = "Allow"

      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }

      Action = "sts:AssumeRole"
    }]
  })

  tags = {
    Project     = "acmecorp-platform"
    Environment = "dev"
  }
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_cloudwatch_log_group" "payments_api" {
  name              = "/ecs/acmecorp/payments-api"
  retention_in_days = 7

  tags = {
    Project     = "acmecorp-platform"
    Environment = "dev"
  }
}

resource "aws_ecs_task_definition" "payments_api" {
  family                   = "acmecorp-payments-api"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"

  cpu    = "256"
  memory = "512"

  execution_role_arn = aws_iam_role.ecs_task_execution.arn

  container_definitions = jsonencode([
    {
      name      = "payments-api"
      image     = "${aws_ecr_repository.payments_api.repository_url}:latest"
      essential = true

      portMappings = [
        {
          containerPort = 8001
          hostPort      = 8001
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "OTEL_SERVICE_NAME"
          value = "payments-api"
        },
        {
          name  = "PAYMENTS_FAILURE_RATE"
          value = "0"
        },
        {
          name  = "PAYMENTS_DELAY_SECONDS"
          value = "0"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"

        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.payments_api.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])

  tags = {
    Project     = "acmecorp-platform"
    Environment = "dev"
    Service     = "payments-api"
  }
}

resource "aws_ecs_service" "payments_api" {
  name            = "payments-api"
  cluster         = aws_ecs_cluster.acmecorp.id
  task_definition = aws_ecs_task_definition.payments_api.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets = [
      aws_subnet.public_a.id,
      aws_subnet.public_b.id
    ]

    security_groups = [
      aws_security_group.app.id
    ]

    assign_public_ip = true
  }

  tags = {
    Project     = "acmecorp-platform"
    Environment = "dev"
    Service     = "payments-api"
  }
}