provider "aws" {
  region = var.aws_region
}

data "aws_availability_zones" "available" {
  state = "available"
}

resource "aws_vpc" "acmecorp" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name        = "acmecorp-vpc"
    Project     = "acmecorp-platform"
    Environment = "dev"
  }
}

resource "aws_subnet" "public_a" {
  vpc_id                  = aws_vpc.acmecorp.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true

  tags = {
    Name        = "acmecorp-public-a"
    Project     = "acmecorp-platform"
    Environment = "dev"
    Type        = "public"
  }
}

resource "aws_subnet" "public_b" {
  vpc_id                  = aws_vpc.acmecorp.id
  cidr_block              = "10.0.2.0/24"
  availability_zone       = data.aws_availability_zones.available.names[1]
  map_public_ip_on_launch = true

  tags = {
    Name        = "acmecorp-public-b"
    Project     = "acmecorp-platform"
    Environment = "dev"
    Type        = "public"
  }
}

resource "aws_subnet" "private_a" {
  vpc_id            = aws_vpc.acmecorp.id
  cidr_block        = "10.0.11.0/24"
  availability_zone = data.aws_availability_zones.available.names[0]

  tags = {
    Name        = "acmecorp-private-a"
    Project     = "acmecorp-platform"
    Environment = "dev"
    Type        = "private"
  }
}

resource "aws_subnet" "private_b" {
  vpc_id            = aws_vpc.acmecorp.id
  cidr_block        = "10.0.12.0/24"
  availability_zone = data.aws_availability_zones.available.names[1]

  tags = {
    Name        = "acmecorp-private-b"
    Project     = "acmecorp-platform"
    Environment = "dev"
    Type        = "private"
  }
}

resource "aws_internet_gateway" "acmecorp" {
  vpc_id = aws_vpc.acmecorp.id

  tags = {
    Name        = "acmecorp-igw"
    Project     = "acmecorp-platform"
    Environment = "dev"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.acmecorp.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.acmecorp.id
  }

  tags = {
    Name        = "acmecorp-public-rt"
    Project     = "acmecorp-platform"
    Environment = "dev"
  }
}

resource "aws_route_table_association" "public_a" {
  subnet_id      = aws_subnet.public_a.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "public_b" {
  subnet_id      = aws_subnet.public_b.id
  route_table_id = aws_route_table.public.id
}

resource "aws_security_group" "app" {
  name        = "acmecorp-app-sg"
  description = "Security group for AcmeCorp application services"
  vpc_id      = aws_vpc.acmecorp.id

  tags = {
    Name        = "acmecorp-app-sg"
    Project     = "acmecorp-platform"
    Environment = "dev"
  }
}

resource "aws_vpc_security_group_egress_rule" "app_all" {
  security_group_id = aws_security_group.app.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

resource "aws_security_group" "database" {
  name        = "acmecorp-database-sg"
  description = "Security group for AcmeCorp database"
  vpc_id      = aws_vpc.acmecorp.id

  tags = {
    Name        = "acmecorp-database-sg"
    Project     = "acmecorp-platform"
    Environment = "dev"
  }
}

resource "aws_vpc_security_group_ingress_rule" "database_from_app" {
  security_group_id            = aws_security_group.database.id
  referenced_security_group_id = aws_security_group.app.id

  from_port   = 5432
  to_port     = 5432
  ip_protocol = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "payments_api_http" {
  security_group_id = aws_security_group.app.id

  cidr_ipv4   = "0.0.0.0/0"
  from_port   = 8001
  to_port     = 8001
  ip_protocol = "tcp"

  description = "Temporary public access to payments API"
}