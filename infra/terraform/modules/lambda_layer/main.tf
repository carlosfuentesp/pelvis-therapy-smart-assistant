variable "layer_name"  { 
    type = string 
}

variable "source_dir"  { 
    type = string 
} # carpeta que contiene un subdir 'python/'

variable "tags"        { 
    type = map(string) 
}

data "archive_file" "zip" {
  type        = "zip"
  source_dir  = var.source_dir
  output_path = "${path.module}/layer.zip"
}

resource "aws_lambda_layer_version" "this" {
  layer_name          = var.layer_name
  filename            = data.archive_file.zip.output_path
  compatible_runtimes = ["python3.12"]
  description         = "Google Calendar deps"
  license_info        = "Apache-2.0"
}

output "layer_arn" { 
    value = aws_lambda_layer_version.this.arn 
}