locals {
  app_dir = abspath("${path.module}/..")

  # Tag the image by a hash of its inputs so Terraform only rebuilds when the app changes.
  source_files = setunion(fileset(local.app_dir, "src/**/*.py"), toset(["Dockerfile", "pyproject.toml", "README.md"]))
  source_hash  = sha1(join("", [for f in sort(tolist(local.source_files)) : filesha1("${local.app_dir}/${f}")]))
}

resource "docker_image" "pipeline" {
  name = "${aws_ecr_repository.pipeline.repository_url}:${local.source_hash}"

  build {
    context    = local.app_dir
    dockerfile = "Dockerfile"
    platform   = "linux/arm64"
  }
}

resource "docker_registry_image" "pipeline" {
  name = docker_image.pipeline.name
}
