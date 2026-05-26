class Scrop < Formula
  desc "Crop sub-images (photos, sticky notes, receipts) out of a scanned composite image"
  homepage "https://github.com/dfla-me/scrop"
  url "https://github.com/dfla-me/scrop/archive/refs/tags/REPLACE_WITH_TAG.tar.gz"
  sha256 "REPLACE_WITH_SHA256_OF_TAGGED_TARBALL"
  license "MIT"

  depends_on "python@3.14"

  # Python dependencies are declared per-platform because the wheels for
  # numpy and opencv-python-headless are precompiled binaries.
  # To bump versions: update the URL+SHA pairs from
  #   https://pypi.org/pypi/<pkg>/<version>/json
  # Look for cp314-cp314 wheels (numpy) or cp37-abi3 wheels
  # (opencv-python-headless, stable ABI: one wheel works for all py3 versions).

  on_macos do
    on_arm do
      resource "numpy" do
        url "https://files.pythonhosted.org/packages/8e/62/764ce66fa4147ae6d73071a3abf804ffe606f174618697c571acdf26a7c9/numpy-2.4.6-cp314-cp314-macosx_11_0_arm64.whl"
        sha256 "38efbc8de75c7a0fc1ac190162d892787f3f47b57cc291231aafee36b80982b7"
      end

      resource "opencv-python-headless" do
        url "https://files.pythonhosted.org/packages/79/42/2310883be3b8826ac58c3f2787b9358a2d46923d61f88fedf930bc59c60c/opencv_python_headless-4.13.0.92-cp37-abi3-macosx_13_0_arm64.whl"
        sha256 "1a7d040ac656c11b8c38677cc8cccdc149f98535089dbe5b081e80a4e5903209"
      end
    end

    on_intel do
      resource "numpy" do
        url "https://files.pythonhosted.org/packages/03/71/21cf70dc6ea3e3acb95fc53a265b2fc248b981f0194ceb5b475271b8809d/numpy-2.4.6-cp314-cp314-macosx_14_0_x86_64.whl"
        sha256 "0a041d3d761dc3c35cc56ce0351506a02bcbc25f7b169f652435141a17db9096"
      end

      resource "opencv-python-headless" do
        url "https://files.pythonhosted.org/packages/2d/1e/6f9e38005a6f7f22af785df42a43139d0e20f169eb5787ce8be37ee7fcc9/opencv_python_headless-4.13.0.92-cp37-abi3-macosx_14_0_x86_64.whl"
        sha256 "3e0a6f0a37994ec6ce5f59e936be21d5d6384a4556f2d2da9c2f9c5dc948394c"
      end
    end
  end

  on_linux do
    on_arm do
      resource "numpy" do
        url "https://files.pythonhosted.org/packages/d5/91/64288395ee1799bd2e0b04a305dce9666da90c961e1f3fe982a05ee1c036/numpy-2.4.6-cp314-cp314-manylinux_2_27_aarch64.manylinux_2_28_aarch64.whl"
        sha256 "40fdc1ae7125e518ea98e53e69a4ebc27e1fd50510c47b7ea130cf21e5e1d42b"
      end

      resource "opencv-python-headless" do
        url "https://files.pythonhosted.org/packages/8f/b4/b7bcbf7c874665825a8c8e1097e93ea25d1f1d210a3e20d4451d01da30aa/opencv_python_headless-4.13.0.92-cp37-abi3-manylinux_2_28_aarch64.whl"
        sha256 "eb60e36b237b1ebd40a912da5384b348df8ed534f6f644d8e0b4f103e272ba7d"
      end
    end

    on_intel do
      resource "numpy" do
        url "https://files.pythonhosted.org/packages/f3/eb/ebffaa97dc55502df69584a8f0dcf07f69a3e0b3e2323670a2722db9aa39/numpy-2.4.6-cp314-cp314-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl"
        sha256 "a2c306dea656c12c68f51f4cea133cbe78ca7435eb28c735eac1d3ebe73be6e8"
      end

      resource "opencv-python-headless" do
        url "https://files.pythonhosted.org/packages/4b/33/b5db29a6c00eb8f50708110d8d453747ca125c8b805bc437b289dbdcc057/opencv_python_headless-4.13.0.92-cp37-abi3-manylinux_2_28_x86_64.whl"
        sha256 "0bd48544f77c68b2941392fcdf9bcd2b9cdf00e98cb8c29b2455d194763cf99e"
      end
    end
  end

  def install
    py = Formula["python@3.14"].opt_bin/"python3.14"

    # Create an isolated venv (no system_site_packages, no pip).
    system py, "-m", "venv", "--without-pip", libexec

    # We deliberately bypass Homebrew's `Language::Python::Virtualenv`
    # helpers here because they pass `--no-binary=:all:` to pip, which
    # refuses to install the precompiled wheels we declare above (and
    # building opencv-python-headless from sdist is impractical — it
    # would compile OpenCV from source).
    pip_install = [
      py, "-m", "pip",
      "--python=#{libexec}/bin/python",
      "--disable-pip-version-check",
      "install",
      "--no-deps"
    ]

    # Install each pre-fetched wheel. Homebrew caches downloads as
    # `<sha>--<original-name>.whl`, but pip's wheel filename parser splits on
    # "-" and rejects the SHA-prefixed form. Copy each wheel into the build
    # directory with its original PyPI filename first.
    resources.each do |r|
      wheel_name = r.cached_download.basename.to_s.sub(/\A[a-f0-9]+--/, "")
      wheel_path = buildpath/wheel_name
      cp r.cached_download, wheel_path
      system(*pip_install, wheel_path.to_s)
    end

    # Install scrop itself from the source tree.
    system(*pip_install, buildpath.to_s)

    bin.install_symlink libexec/"bin/scrop"
  end

  test do
    assert_match "usage: scrop", shell_output("#{bin}/scrop --help")
  end
end
