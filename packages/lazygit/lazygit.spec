%global goipath         github.com/jesseduffield/lazygit
Version:        0.66.2

%gometa -L -f

%bcond_with check

Name:           lazygit
Release:        1%{?dist}
Summary:        Simple terminal UI for git commands

License:        MIT
URL:            https://github.com/jesseduffield/lazygit
Source0:        %{gosource}
Source1:        %{archivename}-vendor.tar.bz2

Recommends:     bash-completion
Recommends:     git

BuildRequires:  go-vendor-tools

%generate_buildrequires
%go_vendor_license_buildrequires

%description
A simple terminal UI for git commands, written in Go with the gocui library.
It offers a keyboard-driven interface for staging, committing, branching,
rebasing and interacting with the reflog, stash and worktrees.

%prep
%goprep -p1
tar -xf %{S:1}

%build
%global gomodulesmode GO111MODULE=on
%gobuild -o %{gobuilddir}/bin/lazygit -ldflags "-X main.version=%{version}" %{goipath}

%install
%go_vendor_license_install
install -m 0755 -vd                     %{buildroot}%{_bindir}
install -m 0755 -vp %{gobuilddir}/bin/* %{buildroot}%{_bindir}/

%{gobuilddir}/bin/lazygit completion bash > lazygit.bash
%{gobuilddir}/bin/lazygit completion zsh  > _lazygit
%{gobuilddir}/bin/lazygit completion fish > lazygit.fish
install -Dpm644 lazygit.bash %{buildroot}%{bash_completions_dir}/lazygit
install -Dpm644 _lazygit     %{buildroot}%{zsh_completions_dir}/_lazygit
install -Dpm644 lazygit.fish %{buildroot}%{fish_completions_dir}/lazygit.fish

%if %{with check}
%check
%gocheck2
%endif

%files -f %{go_vendor_license_filelist}
%doc README.md
%{_bindir}/lazygit
%{bash_completions_dir}/lazygit
%dir %{_datadir}/zsh
%dir %{_datadir}/zsh/site-functions
%{zsh_completions_dir}/_lazygit
%dir %{_datadir}/fish
%dir %{_datadir}/fish/vendor_completions.d
%{fish_completions_dir}/lazygit.fish

%changelog
* Fri Oct 16 2026 Caio Bruno <cbrunofb@gmail.com> - 0.66.2-1
- Initial package
