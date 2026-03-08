ULTRAHDR_VENDOR_DIR ?= vendor/libultrahdr-wasm
ULTRAHDR_BUILD_DIR ?= $(ULTRAHDR_VENDOR_DIR)/build
ULTRAHDR_PUBLIC_DIR ?= public/ultrahdr
ULTRAHDR_BUILD_CMD ?= meson setup build --cross-file=em.txt --wipe && meson compile -C build libultrahdr-esm
ULTRAHDR_CROSS_FILE ?= $(ULTRAHDR_VENDOR_DIR)/em.txt
ULTRAHDR_MODULE ?= libultrahdr-esm.js
ULTRAHDR_EM_CACHE ?= $(abspath $(ULTRAHDR_VENDOR_DIR)/.emscripten_cache)
ULTRAHDR_WRAP_CACHE ?= $(ULTRAHDR_VENDOR_DIR)/subprojects/packagecache
ULTRAHDR_TURBOJPEG_TARBALL ?= $(ULTRAHDR_WRAP_CACHE)/libjpeg-turbo-3.0.0.tar.gz
ULTRAHDR_TURBOJPEG_PATCH ?= $(ULTRAHDR_WRAP_CACHE)/libjpeg-turbo_3.0.0-5_patch.zip

.PHONY: ultrahdr
ultrahdr:
	@if [ ! -d "$(ULTRAHDR_VENDOR_DIR)" ]; then \
		echo "Missing $(ULTRAHDR_VENDOR_DIR). Clone libultrahdr-wasm first."; \
		exit 1; \
	fi
	@if ! command -v emcc >/dev/null 2>&1; then \
		echo "emcc not found. Install emscripten and ensure emcc is in PATH."; \
		exit 1; \
	fi
	@if [ ! -f "$(ULTRAHDR_CROSS_FILE)" ]; then \
		printf "%s\n" "[binaries]" \
		  "c = 'emcc'" \
		  "cpp = 'em++'" \
		  "ar = 'emar'" \
		  "nm = 'emnm'" \
		  "" \
		  "[host_machine]" \
		  "system = 'emscripten'" \
		  "cpu_family = 'wasm32'" \
		  "cpu = 'wasm32'" \
		  "endian = 'little'" \
		  > $(ULTRAHDR_CROSS_FILE); \
	fi
	@if [ ! -f "$(ULTRAHDR_TURBOJPEG_TARBALL)" ] || [ ! -f "$(ULTRAHDR_TURBOJPEG_PATCH)" ]; then \
		echo "Missing libjpeg-turbo wrap sources. Place these files in $(ULTRAHDR_WRAP_CACHE):"; \
		echo "  - libjpeg-turbo-3.0.0.tar.gz"; \
		echo "  - libjpeg-turbo_3.0.0-5_patch.zip"; \
		exit 1; \
	fi
	@mkdir -p $(ULTRAHDR_EM_CACHE)
	cd $(ULTRAHDR_VENDOR_DIR) && EM_CACHE=$(ULTRAHDR_EM_CACHE) EMCC_CACHE=$(ULTRAHDR_EM_CACHE) sh -c "$(ULTRAHDR_BUILD_CMD)"
	@if [ ! -d "$(ULTRAHDR_BUILD_DIR)" ]; then \
		echo "Missing build output at $(ULTRAHDR_BUILD_DIR). Update ULTRAHDR_BUILD_DIR."; \
		exit 1; \
	fi
	@if [ ! -f "$(ULTRAHDR_BUILD_DIR)/$(ULTRAHDR_MODULE)" ]; then \
		echo "Missing $(ULTRAHDR_MODULE) in $(ULTRAHDR_BUILD_DIR). Update ULTRAHDR_MODULE."; \
		exit 1; \
	fi
	@mkdir -p $(ULTRAHDR_PUBLIC_DIR)
	@cp -R $(ULTRAHDR_BUILD_DIR)/*.js $(ULTRAHDR_PUBLIC_DIR)/
	@cp -R $(ULTRAHDR_BUILD_DIR)/*.wasm $(ULTRAHDR_PUBLIC_DIR)/
