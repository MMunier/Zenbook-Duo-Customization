#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>

#include <sys/inotify.h>
#include <linux/limits.h>

#define BACKLIGHT_PATH "/sys/class/backlight/intel_backlight/"
#define SCREENPAD_PATH "/sys/class/leds/asus::screenpad/"
#define EVENT_READ_SIZE (sizeof(struct inotify_event) + NAME_MAX + 1)

long fetch_int_value(char *path) {
    int fd = open(path, O_RDONLY, 0);
    if (fd < 0) {
        return -1;
    }

    char brightness_buf[32];
    memset(&brightness_buf, 0, sizeof(brightness_buf));
    if (0 >= read(fd, &brightness_buf, sizeof(brightness_buf) -1)) {
        close(fd);
        return -1;
    }
    close(fd);
    return atol(brightness_buf);
}

long write_int_value(char *path, long value_to_write) {
    int fd = open(path, O_WRONLY, 0);
    if (fd < 0) {
        return -1;
    }

    char brightness_buf[32];
    sprintf(brightness_buf, "%ld", value_to_write);
    
    size_t len = strlen(brightness_buf);
    if (0 >= write(fd, &brightness_buf, len)) {
        close(fd);
        return -1;
    }
    close(fd);
    return atol(brightness_buf);
}


int main(int argc, const char* argv[]) {

    // Get max brightness
    long BACKLIGHT_MAX_BRIGHTNESS = fetch_int_value(BACKLIGHT_PATH "max_brightness");
    if (BACKLIGHT_MAX_BRIGHTNESS < 0) {
        perror("Failed to fetch BACKLIGHT_MAX_BRIGHTNESS");
        return -1;
    }
    long SCREENPAD_MAX_BRIGHTNESS = fetch_int_value(SCREENPAD_PATH "max_brightness");
    if (SCREENPAD_MAX_BRIGHTNESS < 0) {
        perror("Failed to fetch SCREENPAD_MAX_BRIGHTNESS");
        return -1;
    }

    double brightness_ratio = ((double) SCREENPAD_MAX_BRIGHTNESS) / ((double) BACKLIGHT_MAX_BRIGHTNESS); 

    int inotify_fd = inotify_init();
    if (inotify_fd < 0) {
        perror("Failed to add inotify_fd");
        return -1;
    }

    char event_buf[EVENT_READ_SIZE];
    int watch_fd = inotify_add_watch(inotify_fd, BACKLIGHT_PATH "brightness", IN_MODIFY);
    if (watch_fd < 0) {
        perror("Couldn't add watch to file!");
        return -1;
    }

    // Just pick anything at random =! 0
    long syncronized_screenpad_brightness = 128;

    while (1) {
        int event_read = read(inotify_fd, &event_buf, sizeof(event_buf));
        if (event_read <= 0) {
            perror("Failed to fetch modify_event");
            return -1;
        }

        long backlight_brightness = fetch_int_value(BACKLIGHT_PATH "brightness");
        if (backlight_brightness < 0) {
            perror("Failed to fetch Backlight Brightness!");
            return -1;
        }
        
        long screenpad_brightness = fetch_int_value(SCREENPAD_PATH "brightness");
        if (screenpad_brightness < 0) {
            perror("Failed to fetch Backlight Brightness!");
            return -1;
        }

        // Is the screenpad turned off? Don't change the brightness
        // If we outselves turned if off however feel free to turn it back on
        if (screenpad_brightness == 0 && syncronized_screenpad_brightness != 0) {
            continue;
        }    

        double target_brightness = brightness_ratio * (double) backlight_brightness;
        printf("Writing brightness: %ld (max: %ld)\n", (long) target_brightness, SCREENPAD_MAX_BRIGHTNESS);
        if (0 > write_int_value(SCREENPAD_PATH "brightness", (long) target_brightness)) {
            perror("Failed to write new brightness");
            return -1;
        }

        syncronized_screenpad_brightness = (long) target_brightness;
    }
}
