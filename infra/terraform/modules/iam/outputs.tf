output "workload_role_arn" {
  description = "IAM role ARN for the application workload."
  value       = aws_iam_role.workload.arn
}

output "workload_role_name" {
  description = "IAM workload role name."
  value       = aws_iam_role.workload.name
}
