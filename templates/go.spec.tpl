%global goipath         __GOIPATH__
Version:        __VERSION__

%gometa -L -f

%bcond_without check

Name:           __NAME__
Release:        1%{?dist}
Summary:        __SUMMARY__

License:        __LICENSE__
URL:            __URL__
Source0:        %{gosource}
Source1:        %{archivename}-vendor.tar.bz2

BuildRequires:  go-vendor-tools

%generate_buildrequires
%go_vendor_license_buildrequires

%description
__SUMMARY__

%prep
%goprep -p1
tar -xf %{S:1}

%build
%global gomodulesmode GO111MODULE=on
# Optional version stamping: -ldflags "-X main.version=%{version}"
%gobuild -o %{gobuilddir}/bin/__NAME__ %{goipath}

%install
%go_vendor_license_install
install -m 0755 -vd                     %{buildroot}%{_bindir}
install -m 0755 -vp %{gobuilddir}/bin/* %{buildroot}%{_bindir}/

# Optional: generate completions by running the just-built binary
#%{gobuilddir}/bin/__NAME__ completion bash > __NAME__.bash
#install -Dpm644 __NAME__.bash %{buildroot}%{bash_completions_dir}/__NAME__

%if %{with check}
%check
%gocheck2
%endif

%files -f %{go_vendor_license_filelist}
%doc README.md
%{_bindir}/__NAME__

%changelog
* __DATE__ __PACKAGER__ - __VERSION__-1
- Initial package
