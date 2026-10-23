Name:           fish-done
Version:        1.21.1
Release:        1%{?dist}
Summary:        Notifications when long-running fish commands finish
BuildArch:      noarch

License:        MIT
URL:            https://github.com/franciscolourenco/done
Source0:        https://github.com/franciscolourenco/done/archive/refs/tags/1.21.1.tar.gz

BuildRequires:  fish
Requires:       fish

%description
Notifications when long-running fish commands finish

%prep
%autosetup -n done-%{version}

%build

%install
install_vendor() {
  # $2: vendor subdir; conf.d already ends in .d, the others do not
  [ -d "$1" ] || return 0
  for f in "$1"/*.fish; do
    install -Dpm644 "$f" "%{buildroot}%{_datadir}/fish/vendor_$2/$(basename "$f")"
  done
}
install_vendor conf.d conf.d
install_vendor functions functions.d
install_vendor completions completions.d

%check
for f in conf.d/*.fish functions/*.fish completions/*.fish; do
  if [ -f "$f" ]; then
    fish -n "$f"
  fi
done

%files
%license LICENSE
%{_datadir}/fish/vendor_conf.d/*.fish

%changelog
* Sat Oct 17 2026 Caio Bruno <cbrunofb@gmail.com> - 1.21.1-1
- Initial package