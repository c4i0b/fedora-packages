Name:           ccze
Version:        0.2.1
Release:        1%{?dist}
Summary:        A robust and modular log colorizer

License:        GPL-2.0-or-later
URL:            http://bonehunter.rulez.org/CCZE.html
# Upstream FTP is long dead; the Debian pool keeps the pristine 0.2.1 tarball
Source0:        https://deb.debian.org/debian/pool/main/c/ccze/ccze_%{version}.orig.tar.gz
# PCRE1 is gone from current distros: build against PCRE2 through a shim
Source1:        pcre2-compat.h
# Downstream patches carried since the Fedora package (upstream is dead)
Patch0:         ccze-0.2.1-Wmulticharacter.patch
Patch1:         ccze-opts.diff
Patch2:         ccze-configure-c99.patch

BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  ncurses-devel >= 5.0
BuildRequires:  pcre2-devel

%description
CCZE is a robust and modular log colorizer, with plugins for apm,
exim, fetchmail, httpd, postfix, procmail, squid, syslog, ulogd,
vsftpd, xferlog and more. It is a drop-in replacement for colorize.

%prep
%autosetup -n ccze-%{version} -p1

iconv -f ISO-8859-1 -t UTF-8 THANKS > THANKS.new
touch --reference THANKS THANKS.new
mv -f THANKS.new THANKS

%build
# configure probes pcre via pcre-config (PCRE1-only): give it a wrapper that
# points the include path at the shim and the lib at pcre2-8
mkdir -p shim
cp -p %{SOURCE1} shim/pcre.h
cat > pcre-config <<'EOF'
#!/bin/sh
case "$1" in
  --cflags) echo "-I$(dirname "$0")/shim" ;;
  --libs)   echo "-lpcre2-8" ;;
esac
EOF
chmod +x pcre-config
PATH="$PWD:$PATH" %configure --with-builtins=all
# errno_t is already defined in glibc's errno.h
%make_build CFLAGS="%{optflags} -D__error_t_defined=1"

%install
%make_install

src/ccze-dump > cczerc
install -Dpm0644 -t %{buildroot}%{_sysconfdir} cczerc

rm %{buildroot}%{_includedir}/ccze.h

%check
%{buildroot}%{_bindir}/ccze --version >/dev/null

%files
%doc AUTHORS ChangeLog ChangeLog-0.1 NEWS README THANKS FAQ
%license COPYING
%config(noreplace) %{_sysconfdir}/cczerc
%{_bindir}/ccze
%{_bindir}/ccze-cssdump
%{_mandir}/man1/ccze.1*
%{_mandir}/man1/ccze-cssdump.1*
%{_mandir}/man7/ccze-plugin.7*

%changelog
* Sun Oct 18 2026 Caio Bruno <cbrunofb@gmail.com> - 0.2.1-1
- Initial package (retired from Fedora rawhide; hollywood's widgets exit without it)
