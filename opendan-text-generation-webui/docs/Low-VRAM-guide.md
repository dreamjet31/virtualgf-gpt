If you GPU is not large enough to fit a model, try these in the following order:

### Load the model in 8-bit mode

```
python server.py --load-in-8bit
```

This reduces the memory usage by half with no noticeable loss in quality. Only newer GPUs support 8-bit mode.

### Split the model across your GPU and CPU

```
python server.py --auto-devices
```

If you can load the model with this command but it runs out of memory when you try to generate text, try increasingly limiting the amount of memory allocated to the GPU until the error stops happening:

```
python server.py --auto-devices --gpu-memory 10
python server.py --auto-devices --gpu-memory 9
python server.py --auto-devices --gpu-memory 8
...
```

where the number is in GiB.

For finer control, you can also specify the unit in MiB explicitly:

```
python server.py --auto-devices --gpu-memory 8722MiB
python server.py --auto-devices --gpu-memory 4725MiB
python server.py --auto-devices --gpu-memory 3500MiB
...
```

Additionally, you can also set the `--no-cache` value to reduce the GPU usage while generating text at a performance cost. This may allow you to set a higher value for `--gpu-memory`, resulting in a net performance gain.

### Send layers to a disk cache

As a desperate last measure, you can split the model across your GPU, CPU, and disk:

```
python server.py --auto-devices --disk
```

With this, I am able to load a 30b model into my RTX 3090, but it takes 10 seconds to generate 1 word.

### DeepSpeed (experimental)

An experimental alternative to all of the above is to use DeepSpeed: [guide](DeepSpeed.md).
