Name:		google-oauth-client
Version:	1.34.1
Release:	1
Summary:	Google OAuth client for Java
Group:		Development/Java
License:	Apache-2.0
URL:		https://github.com/googleapis/google-oauth-java-client
# Tag v1.34.1. The archive has no prebuilt jars or class files.
Source0:	https://github.com/googleapis/google-oauth-java-client/archive/refs/tags/v%{version}.tar.gz#/google-oauth-client-%{version}.tar.gz

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
OAuth 1 and OAuth 2 client used by the Google API client. Gradle 9.9.1
strictly pins %{version}. The servlet, Jetty, and App Engine modules are
not built. Google HTTP Client is class version 55, so this jar is Java 11.

%prep
%autosetup -n google-oauth-java-client-%{version}
find . \( -name '*.jar' -o -name '*.class' -o -name '*.so' -o -name '*.node' -o -name '*.wasm' \) -delete

%build
set -eo pipefail
find google-oauth-client/src/main/java -name '*.java' ! -name 'module-info.java' > sources.list
test "$(wc -l < sources.list)" -eq 40
mkdir -p classes
CP=%{_javadir}/google-http-client.jar:%{_javadir}/google-http-client-gson.jar:%{_javadir}/gson-2.14.0.jar:%{_javadir}/guava.jar:%{_javadir}/failureaccess.jar
javac --release 11 -encoding UTF-8 -Xlint:-options -cp "$CP" -d classes @sources.list
cat > manifest.mf << 'EOF'
Manifest-Version: 1.0
Automatic-Module-Name: com.google.api.client.auth

EOF
jar cfm google-oauth-client.jar manifest.mf -C classes .
jar i google-oauth-client.jar
javap -verbose -cp google-oauth-client.jar com.google.api.client.auth.oauth2.TokenResponse | grep -F 'major version: 55'

cat > google-oauth-client.pom << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.google.oauth-client</groupId>
  <artifactId>google-oauth-client</artifactId>
  <version>1.34.1</version>
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

%install
sysjar install --buildroot %{buildroot} \
	--artifact google-oauth-client.pom:google-oauth-client.jar \
	--file-name google-oauth-client \
	--filelist .mfiles

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
JAR=%{buildroot}%{_javadir}/google-oauth-client.jar
test -f "$JAR"
CP="$JAR:%{_javadir}/google-http-client.jar:%{_javadir}/google-http-client-gson.jar:%{_javadir}/gson-2.14.0.jar:%{_javadir}/guava.jar:%{_javadir}/failureaccess.jar"
javac --release 11 -encoding UTF-8 -Xlint:-options -cp "$CP" -d check check/Smoke.java
java -cp "check:$CP" Smoke > check/out.txt
cat check/out.txt
grep -F -q 'goauth_ok gradle Bearer' check/out.txt

%files -f .mfiles
%doc LICENSE README.md
