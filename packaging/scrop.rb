class Scrop < Formula
  include Language::Python::Virtualenv

  desc "Crop sub-images (photos, sticky notes, receipts) out of a scanned composite image"
  homepage "https://github.com/dfla-me/scrop"
  url "https://github.com/dfla-me/scrop/archive/refs/tags/v0.1.0.tar.gz"
  sha256 "REPLACE_WITH_SHA256_OF_TAGGED_TARBALL"
  license "MIT"

  depends_on "numpy"
  depends_on "opencv"
  depends_on "python@3.13"

  def install
    venv = virtualenv_create(libexec, "python3.13", system_site_packages: true)
    venv.pip_install_and_link buildpath
  end

  test do
    assert_match "usage: scrop", shell_output("#{bin}/scrop --help")
  end
end
