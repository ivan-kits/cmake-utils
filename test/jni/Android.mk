LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)
LOCAL_MODULE := c_shared
LOCAL_SRC_FILES := ../shared/shared.c
include $(BUILD_SHARED_LIBRARY)

include $(CLEAR_VARS)
LOCAL_MODULE := c_static
LOCAL_SRC_FILES := ../static/static.c
include $(BUILD_STATIC_LIBRARY)

C_SHARED_LIBRARIES := c_shared
C_STATIC_LIBRARIES := c_static

ifeq ($(APP_STL), none)
	CPP_FLAGS := -DNONE
else ifeq ($(APP_STL), system)
	CPP_FLAGS := -DSYSTEM
else
	include $(CLEAR_VARS)
	LOCAL_MODULE := cpp_shared
	LOCAL_SRC_FILES := ../shared/shared.cpp
	include $(BUILD_SHARED_LIBRARY)

	include $(CLEAR_VARS)
	LOCAL_MODULE := cpp_static
	LOCAL_SRC_FILES := ../static/static.cpp
	include $(BUILD_STATIC_LIBRARY)

	CPP_SHARED_LIBRARIES := cpp_shared
	CPP_STATIC_LIBRARIES := cpp_static
endif

include $(CLEAR_VARS)
LOCAL_MODULE := c_exe
LOCAL_SRC_FILES := ../exe.c
LOCAL_SHARED_LIBRARIES := $(C_SHARED_LIBRARIES)
LOCAL_STATIC_LIBRARIES := $(C_STATIC_LIBRARIES)
include $(BUILD_EXECUTABLE)

include $(CLEAR_VARS)
LOCAL_MODULE := cpp_exe
LOCAL_SRC_FILES := ../exe.cpp
LOCAL_CPPFLAGS := $(CPP_FLAGS)
LOCAL_SHARED_LIBRARIES := $(C_SHARED_LIBRARIES) $(CPP_SHARED_LIBRARIES)
LOCAL_STATIC_LIBRARIES := $(C_STATIC_LIBRARIES) $(CPP_STATIC_LIBRARIES)
include $(BUILD_EXECUTABLE)
