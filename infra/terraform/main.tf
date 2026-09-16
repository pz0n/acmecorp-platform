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