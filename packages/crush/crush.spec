%global goipath         github.com/charmbracelet/crush
Version:        0.98.1

%gometa -L -f

%bcond_with check

Name:           crush
Release:        1%{?dist}
Summary:        Agentic coding assistant for the terminal

License:        FSL-1.1-MIT
URL:            https://github.com/charmbracelet/crush
Source0:        %{gosource}
Source1:        %{archivename}-vendor.tar.bz2

BuildRequires:  go-vendor-tools

%generate_buildrequires
%go_vendor_license_buildrequires

%description
A powerful terminal-based AI assistant for developers, providing
intelligent coding assistance directly in your terminal. Supports a wide
range of LLM providers, LSP integration for context, MCP servers and
session management.

%prep
%goprep -p1
tar -xf %{S:1}

%build
%global gomodulesmode GO111MODULE=on
# f43/f44 ship go 1.26 while go.mod requires 1.27; fetch the toolchain at build time (network is on)
export GOTOOLCHAIN=auto
%gobuild -o %{gobuilddir}/bin/crush -ldflags "-X github.com/charmbracelet/crush/internal/version.Version=%{version}" %{goipath}

%install
%go_vendor_license_install
install -m 0755 -vd                     %{buildroot}%{_bindir}
install -m 0755 -vp %{gobuilddir}/bin/* %{buildroot}%{_bindir}/

%{gobuilddir}/bin/crush completion bash > crush.bash
%{gobuilddir}/bin/crush completion zsh  > _crush
%{gobuilddir}/bin/crush completion fish > crush.fish
install -Dpm644 crush.bash %{buildroot}%{bash_completions_dir}/crush
install -Dpm644 _crush     %{buildroot}%{zsh_completions_dir}/_crush
install -Dpm644 crush.fish %{buildroot}%{fish_completions_dir}/crush.fish

%{gobuilddir}/bin/crush man > crush.1
install -Dpm644 crush.1 %{buildroot}%{_mandir}/man1/crush.1

%if %{with check}
%check
%gocheck2
%endif

%files -f %{go_vendor_license_filelist}
%doc README.md
%{_bindir}/crush
%{bash_completions_dir}/crush
%dir %{_datadir}/zsh
%dir %{_datadir}/zsh/site-functions
%{zsh_completions_dir}/_crush
%dir %{_datadir}/fish
%dir %{_datadir}/fish/vendor_completions.d
%{fish_completions_dir}/crush.fish
%{_mandir}/man1/crush.1*

%changelog
* Tue Oct 20 2026 Caio Bruno <cbrunofb@gmail.com> - 0.98.1-1
- Initial package
