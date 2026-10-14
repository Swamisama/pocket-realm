cmake_minimum_required(VERSION 3.16)
project(pocket_bot_target_fence_test LANGUAGES CXX)

find_package(Threads REQUIRED)
add_executable(pocket_bot_target_fence_test test_bot_target_fence.cpp)
target_compile_features(pocket_bot_target_fence_test PRIVATE cxx_std_17)
target_include_directories(pocket_bot_target_fence_test PRIVATE ../include)
target_link_libraries(pocket_bot_target_fence_test PRIVATE Threads::Threads)

enable_testing()
add_test(NAME pocket_bot_target_fence_test COMMAND pocket_bot_target_fence_test)

add_executable(pocket_legacy_first_tick_test test_legacy_first_tick.cpp
    ../../pocket-runtime/src/first_tick_fence.cpp)
target_compile_features(pocket_legacy_first_tick_test PRIVATE cxx_std_17)
target_include_directories(pocket_legacy_first_tick_test PRIVATE ../../pocket-runtime/include)
target_link_libraries(pocket_legacy_first_tick_test PRIVATE Threads::Threads)
add_test(NAME pocket_legacy_first_tick_test COMMAND pocket_legacy_first_tick_test)
