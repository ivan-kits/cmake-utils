LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)
LOCAL_MODULE := c_shared
LOCAL_SRC_FILES := ../shared/shared.c
include $(BUILD_SHARED_LIBRARY)

include $(CLEAR_VARS)
LOCAL_MODULE := cpp_shared
LOCAL_SRC_FILES := ../shared/shared.cpp
include $(BUILD_SHARED_LIBRARY)

include $(CLEAR_VARS)
LOCAL_MODULE := c_static
LOCAL_SRC_FILES := ../static/static.c
include $(BUILD_STATIC_LIBRARY)

include $(CLEAR_VARS)
LOCAL_MODULE := cpp_static
LOCAL_SRC_FILES := ../static/static.cpp
include $(BUILD_STATIC_LIBRARY)

include $(CLEAR_VARS)
LOCAL_MODULE := c_exe
LOCAL_SRC_FILES := ../exe.c
LOCAL_SHARED_LIBRARIES := c_shared
LOCAL_STATIC_LIBRARIES := c_static
include $(BUILD_EXECUTABLE)

include $(CLEAR_VARS)
LOCAL_MODULE := cpp_exe
LOCAL_SRC_FILES := ../exe.cpp
LOCAL_SHARED_LIBRARIES := c_shared cpp_shared
LOCAL_STATIC_LIBRARIES := c_static cpp_static
include $(BUILD_EXECUTABLE)
