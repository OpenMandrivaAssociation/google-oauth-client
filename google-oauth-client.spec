Name:		google-oauth-client
Version:	1.39.0
Release:	1
Summary:	Google OAuth client for Java
Group:		Development/Java
License:	Apache-2.0
URL:		https://github.com/googleapis/google-oauth-java-client
# Tag v1.39.0. The archive has no prebuilt jars or class files.
Source0:	https://github.com/googleapis/google-oauth-java-client/archive/refs/tags/v%{version}.tar.gz#/google-oauth-client-%{version}.tar.gz
# Gradle and the Google API client pin this artifact at 1.34.1.
Source1:	https://github.com/googleapis/google-oauth-java-client/archive/refs/tags/v1.34.1.tar.gz#/google-oauth-client-1.34.1.tar.gz

BuildArch:	noarch
BuildRequires:	java-current-devel
BuildRequires:	sysjar
BuildRequires:	javapackages-filesystem
BuildRequires:	mvn(com.google.http-client:google-http-client)
BuildRequires:	mvn(com.google.http-client:google-http-client-gson)
BuildRequires:	mvn(com.google.code.gson:gson)
BuildRequires:	mvn(com.google.guava:guava)
BuildRequires:	mvn(com.google.guava:failureaccess)

%description
OAuth 1 and OAuth 2 client used by the Google API client. The 1.34.1
jar stays installed beside %{version}. The servlet, Jetty, and App
Engine modules are not built. Google HTTP Client is class version 55,
so this jar is Java 11.

%prep
%autosetup -n google-oauth-java-client-%{version}
tar -xf %{SOURCE1}
find . \( -name '*.jar' -o -name '*.class' -o -name '*.so' -o -name '*.node' -o -name '*.wasm' \) -delete

%build
set -eo pipefail
CP=%{_javadir}/google-http-client.jar:%{_javadir}/google-http-client-gson.jar:%{_javadir}/gson-2.14.0.jar:%{_javadir}/guava.jar:%{_javadir}/failureaccess.jar

write_pom() {
	ver="$1"
	dest="$2"
	cat > "$dest/google-oauth-client.pom" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.google.oauth-client</groupId>
  <artifactId>google-oauth-client</artifactId>
  <version>$ver</version>
  <name>Google OAuth Client</name>
  <description>OAuth client for the Google API client libraries</description>
  <licenses>
    <license>
      <name>Apache-2.0</name>
    </license>
  </licenses>
  <dependencies>
    <dependency>
      <groupId>com.google.http-client</groupId>
      <artifactId>google-http-client</artifactId>
      <version>1.42.2</version>
    </dependency>
    <dependency>
      <groupId>com.google.http-client</groupId>
      <artifactId>google-http-client-gson</artifactId>
      <version>1.42.2</version>
    </dependency>
    <dependency>
      <groupId>com.google.code.gson</groupId>
      <artifactId>gson</artifactId>
      <version>2.14.0</version>
    </dependency>
    <dependency>
      <groupId>com.google.guava</groupId>
      <artifactId>guava</artifactId>
      <version>33.6.0-jre</version>
    </dependency>
  </dependencies>
</project>
EOF
}

build_one() {
	root="$1"
	ver="$2"
	dest="$3"
	mkdir -p "$dest/classes"
	find "$root/google-oauth-client/src/main/java" -name '*.java' ! -name 'module-info.java' > "$dest/sources.list"
	test "$(wc -l < "$dest/sources.list")" -eq 40
	javac --release 11 -encoding UTF-8 -Xlint:-options -cp "$CP" -d "$dest/classes" @"$dest/sources.list"
	cat > "$dest/manifest.mf" << 'EOF'
Manifest-Version: 1.0
Automatic-Module-Name: com.google.api.client.auth

EOF
	jar cfm "$dest/google-oauth-client.jar" "$dest/manifest.mf" -C "$dest/classes" .
	jar i "$dest/google-oauth-client.jar"
	javap -verbose -cp "$dest/google-oauth-client.jar" com.google.api.client.auth.oauth2.TokenResponse | grep -F 'major version: 55'
	write_pom "$ver" "$dest"
}

build_one google-oauth-java-client-1.34.1 1.34.1 out134
build_one . %{version} out
javap -public -cp out/google-oauth-client.jar com.google.api.client.auth.openidconnect.IdTokenVerifier | grep -F 'verifyOrThrow'

%install
set -eo pipefail
sysjar install --buildroot %{buildroot} \
	--artifact out134/google-oauth-client.pom:out134/google-oauth-client.jar \
	--file-name google-oauth-client-1.34.1 \
	--filelist .mfiles134
/bin/mv %{buildroot}/usr/share/sysjar/index/com.google.oauth-client/google-oauth-client.sysjar \
	%{buildroot}/usr/share/sysjar/index/com.google.oauth-client/google-oauth-client-1.34.1.sysjar
sed -i 's|/usr/share/sysjar/index/com.google.oauth-client/google-oauth-client\.sysjar|/usr/share/sysjar/index/com.google.oauth-client/google-oauth-client-1.34.1.sysjar|' .mfiles134
idx134=%{buildroot}/usr/share/sysjar/index/com.google.oauth-client/google-oauth-client-1.34.1.sysjar
test -s "$idx134"
grep -F -q '"version": "1.34.1"' "$idx134"
grep -F -q '"artifactId": "google-oauth-client"' "$idx134"
sysjar install --buildroot %{buildroot} \
	--artifact out/google-oauth-client.pom:out/google-oauth-client.jar \
	--file-name google-oauth-client \
	--filelist .mfiles-new
idx=%{buildroot}/usr/share/sysjar/index/com.google.oauth-client/google-oauth-client.sysjar
test -s "$idx"
grep -F -q '"version": "%{version}"' "$idx"
grep -F -q '"artifactId": "google-oauth-client"' "$idx"
test -s %{buildroot}%{_javadir}/google-oauth-client.jar
test -s %{buildroot}%{_javadir}/google-oauth-client-1.34.1.jar
: > .mfiles
while IFS= read -r line; do
	grep -qxF -- "$line" .mfiles || printf '%s\n' "$line" >> .mfiles
done < .mfiles-new
while IFS= read -r line; do
	grep -qxF -- "$line" .mfiles || printf '%s\n' "$line" >> .mfiles
done < .mfiles134

%check
set -eo pipefail
mkdir -p check
cat > check/Smoke.java << 'EOF'
import com.google.api.client.auth.oauth2.TokenResponse;
import com.google.api.client.json.JsonFactory;
import com.google.api.client.json.gson.GsonFactory;
public class Smoke {
	public static void main(String[] args) throws Exception {
		JsonFactory json = GsonFactory.getDefaultInstance();
		TokenResponse token = json.fromString("{\"access_token\":\"gradle\",\"token_type\":\"Bearer\"}", TokenResponse.class);
		if (!"gradle".equals(token.getAccessToken()) || !"Bearer".equals(token.getTokenType())) {
			throw new RuntimeException(token.getAccessToken() + " " + token.getTokenType());
		}
		System.out.println("goauth_ok " + token.getAccessToken() + " " + token.getTokenType());
	}
}
EOF
DEPS=%{_javadir}/google-http-client.jar:%{_javadir}/google-http-client-gson.jar:%{_javadir}/gson-2.14.0.jar:%{_javadir}/guava.jar:%{_javadir}/failureaccess.jar
run_check() {
	ver="$1"
	jar="$2"
	test -f "$jar"
	/bin/rm -rf "check/$ver"
	mkdir -p "check/$ver"
	classpath="$jar:$DEPS"
	javac --release 11 -encoding UTF-8 -Xlint:-options -cp "$classpath" -d "check/$ver" check/Smoke.java
	java -cp "check/$ver:$classpath" Smoke > "check/$ver/out.txt"
	cat "check/$ver/out.txt"
	grep -F -q 'goauth_ok gradle Bearer' "check/$ver/out.txt"
}
run_check %{version} %{buildroot}%{_javadir}/google-oauth-client.jar
run_check 1.34.1 %{buildroot}%{_javadir}/google-oauth-client-1.34.1.jar

%files -f .mfiles
%doc LICENSE README.md
