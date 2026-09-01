# ~/.config/fish/config.fish

if status is-interactive
    bind ctrl-c 'commandline -f cancel-commandline repaint'
    bind ctrl-left backward-word
    bind ctrl-right forward-word

    function ip --wraps='ip'
        command ip --color=auto $argv
    end

    function push-lineageos-update --wraps='~/Projects/lineage-nio/packages/apps/Updater/push-update.sh'
        ~/Projects/lineage-nio/packages/apps/Updater/push-update.sh $argv
    end

    function update-proxy-config --wraps='sudo python ~/Projects/env/proxy/update-config.py'
        sudo python ~/Projects/env/proxy/update-config.py $argv
    end

    set -x http_proxy http://127.0.0.1:1080
    set -x https_proxy http://127.0.0.1:1080

    . /etc/modules/init/fish
    . /etc/modules/init/fish_completion
    ml use "$HOME/.local/share/modulefiles"
end
