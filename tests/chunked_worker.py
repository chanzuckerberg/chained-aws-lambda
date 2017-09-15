import collections
import itertools
import typing
import uuid

from dss.events.chainedawslambda import Runner, Runtime, Task


class TestStingyRuntime(Runtime[dict, typing.Any]):
    """This is runtime that returns a pre-determined sequence, and then 0s for the remaining time."""
    def __init__(
            self,
            global_results: typing.Mapping[str, typing.Any],
            seq: typing.Optional[typing.Iterable[int]]=None) -> None:
        self.global_results = global_results
        self.result = None  # type: typing.Optional[typing.Any]
        if seq is None:
            seq = list()
        self.seq = itertools.chain(seq, itertools.repeat(0))
        self.scheduled_work = list()  \
            # type: typing.List[typing.Tuple[typing.Type[Task], dict, typing.Optional[str]]]

    def get_remaining_time_in_millis(self) -> int:
        return self.seq.__next__()

    def schedule_work(
            self,
            task_class: typing.Type[Task[typing.Any, typing.Any]],
            state: typing.Any,
            new_task: bool,
    ) -> str:
        # it's illegal for there to be no state.
        assert state is not None

        task_id = str(uuid.uuid4()) if new_task else None
        self.scheduled_work.append((task_class, state, task_id))
        return task_id

    def work_complete_callback(self, result: typing.Any):
        self.result = result


def run_task_to_completion(
        initial_task: typing.Type[Task],
        initial_state: typing.Any,
        runtime_builder: typing.Callable[[typing.Mapping[str, typing.Any]], Runtime],
        task_builder: typing.Callable[[typing.Type[Task], typing.Any, Runtime], Task],
        runtime_result_getter: typing.Callable[[Runtime], typing.Optional[typing.Any]],
        runtime_scheduled_getter: typing.Callable[
            [Runtime], typing.List[typing.Tuple[typing.Type[Task], typing.Any, typing.Optional[str]]]],
) -> typing.Tuple[int, typing.Any]:
    """
    Run through the lifecycle of a task all the way to completion.  The initial task's class and state is passed into
    the method, and various callables must be provided to complete the task.

    :param initial_task: This is the initial task that we're starting with.
    :param initial_state: This is the initial state of the task we're starting with.
    :param runtime_builder: This is a callable that is called to generate a Runtime object.  It is called with a
                            dictionary that stores a mapping between task uuids and their results.
    :param task_builder: This is a callable that produces a Task object, given a task's class, the state, and the
                         runtime.
    :param runtime_result_getter: This is a callable that we execute against a runtime object to get the result of the
                                  task.  If the task is not complete, the callable should return None.
    :param runtime_scheduled_getter: This is a callable that we execute against a runtime object to find all the work
                                     the task has scheduled.  This should produce a list of (task_class, state).
    :return: A tuple containing the number of times the state was frozen and the final result of the task.
    """
    TASK_ID_KEY = "task_id"
    STATE_KEY = "state"

    initial_task_id = str(uuid.uuid4())
    queue = collections.deque()  # type: typing.Deque[typing.Tuple[typing.Type[Task], dict]]
    queue.append((initial_task, {TASK_ID_KEY: initial_task_id, STATE_KEY: initial_state}))
    results = dict()  # type: typing.MutableMapping[str, typing.Any]
    freezes = 0
    while len(queue) > 0:
        task_class, wrapped_state = queue.popleft()

        task_id = wrapped_state[TASK_ID_KEY]
        state = wrapped_state[STATE_KEY]

        runtime = runtime_builder(results)
        task = task_builder(task_class, state, runtime)
        runner = Runner(task, runtime)

        runner.run()

        result = runtime_result_getter(runtime)
        if result is not None:
            if task_id == initial_task_id:
                # we're done!
                return freezes, result
            else:
                results[task_id] = result

        # collect the work that we've queued up.
        for scheduled_task_class, scheduled_task_state, scheduled_task_id in runtime_scheduled_getter(runtime):
            if scheduled_task_id is None:
                scheduled_task_id = task_id
            queue.append((scheduled_task_class, {TASK_ID_KEY: scheduled_task_id, STATE_KEY: scheduled_task_state}))
        freezes += 1

    raise RuntimeError("Queue drained, but task not complete.")
