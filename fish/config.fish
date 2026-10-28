# ~/.config/fish/config.fish

if status is-interactive
    bind ctrl-c 'commandline -f cancel-commandline repaint'
    bind ctrl-left backward-word
    bind ctrl-right forward-word

    function push-lineageos-update --wraps='~/Projects/lineage-nio/packages/apps/Updater/push-update.sh'
        ~/Projects/lineage-nio/packages/apps/Updater/push-update.sh $argv
    end

    function update-proxy-config --wraps='sudo python ~/Projects/env/proxy/update-config.py'
        sudo python ~/Projects/env/proxy/update-config.py $argv
    end

    function opencode-here
        mkdir -p .opencode-data/{cache,config,share,state}
        bwrap \
            --unshare-all \
            --die-with-parent \
            --share-net \
            --ro-bind / / \
            --dev /dev --proc /proc \
            --tmpfs $HOME --tmpfs /run --tmpfs /var --tmpfs /tmp \
            --bind .opencode-data/cache $HOME/.cache/opencode \
            --bind .opencode-data/config $HOME/.config/opencode \
            --bind .opencode-data/share $HOME/.local/share/opencode \
            --bind .opencode-data/state $HOME/.local/state/opencode \
            --bind . $HOME/w \
            --tmpfs $HOME/w/.opencode-data \
            bash -c 'opencode pair && exec bash -i'
    end

    set -x http_proxy http://127.0.0.1:1080
    set -x https_proxy http://127.0.0.1:1080

    . /usr/share/modules/init/fish
    . /usr/share/modules/init/fish_completion
    ml use "$HOME/.local/share/modulefiles"
end
