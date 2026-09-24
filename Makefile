# make assets   regenerate images/ and sounds/ (python3, stdlib only)
# make zip      build out/roku2048.zip
# make install  ROKU_IP=192.168.x.x ROKU_PASS=yourpass  -> sideload to device
# make console  BrightScript debug console (port 8085)
# make check    Roku Static Analysis (needs SCA=path/to/sca-cmd, see below)
# make package  ROKU_IP=... ROKU_PASS=... PKG_PASS=<genkey password>
#               -> signed out/roku2048-<version>.pkg for the developer dashboard
#
# Packaging needs a signing key on the device, created once with:
#   telnet $ROKU_IP 8080   then type:  genkey
# Keep the printed password + DevID safe: every future update of the published
# app must be signed with the same key (use "rekey" to restore it on a device).

ZIP := out/roku2048.zip
VERSION := $(shell awk -F= '/^major_version/{a=$$2}/^minor_version/{b=$$2}/^build_version/{c=$$2}END{print a"."b"."c}' manifest)
SCA ?= sca-cmd
SRC := manifest $(shell find source components images sounds -type f ! -name '.DS_Store')

zip: $(ZIP)

$(ZIP): $(SRC)
	@mkdir -p out
	@rm -f $(ZIP)
	@# -D: no directory entries, -X: no macOS extra attributes (strict validators reject both)
	zip -9 -q -r -D -X $(ZIP) manifest source components images sounds -x '*.DS_Store' -x '*/.*'
	@ls -l $(ZIP)

assets:
	python3 tools/gen_assets.py

install: $(ZIP)
	@test -n "$(ROKU_IP)" || (echo "set ROKU_IP=..." && exit 1)
	curl -sS --digest -u rokudev:$(ROKU_PASS) -F mysubmit=Install -F archive=@$(ZIP) \
		http://$(ROKU_IP)/plugin_install | grep -o '<font color="red">[^<]*' | sed 's/<font color="red">//'

check: $(ZIP)
	$(SCA) $(ZIP) -s warning

package: install
	@test -n "$(PKG_PASS)" || (echo "set PKG_PASS=<genkey password>" && exit 1)
	@curl -sS --digest -u rokudev:$(ROKU_PASS) -F mysubmit=Package -F app_name=2048/$(VERSION) \
		-F passwd=$(PKG_PASS) -F pkg_time=$$(date +%s) http://$(ROKU_IP)/plugin_package -o out/package.html
	@PKG=$$(grep -oE 'pkgs//?[A-Za-z0-9_]+\.pkg' out/package.html | head -1); \
		test -n "$$PKG" || (grep -oE '<font color="red">[^<]*' out/package.html; echo "packaging failed"; exit 1); \
		curl -sS --digest -u rokudev:$(ROKU_PASS) -o out/roku2048-$(VERSION).pkg http://$(ROKU_IP)/$$PKG && \
		ls -l out/roku2048-$(VERSION).pkg

console:
	nc $(ROKU_IP) 8085

clean:
	rm -rf out

.PHONY: zip assets install check package console clean
